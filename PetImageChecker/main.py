import io
import json
import logging
import os
import re
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
except Exception:
    load_dotenv = None

try:
    import psycopg  # type: ignore[import-not-found]
except Exception:
    psycopg = None

try:
    from neo4j import GraphDatabase  # type: ignore[import-not-found]
except Exception:
    GraphDatabase = None

try:
    from openai import OpenAI  # type: ignore[import-not-found]
except Exception:
    OpenAI = None

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if load_dotenv is not None:
    load_dotenv()

# Global model variable
model = None

# COCO dataset class indices
# 15: cat
# 16: dog
ALLOWED_CLASSES = [15, 16]

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading YOLOv8 model...")
    try:
        model = YOLO("yolov8n.pt")
        logger.info("YOLOv8 model loaded successfully.")
    except Exception as ex:
        model = None
        logger.warning("YOLOv8 model failed to load at startup: %s", ex)
    yield
    model = None

app = FastAPI(
    title="Pet Image Verification API",
    description="An API to verify pet images and orchestrate multi-agent symptom analysis.",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return JSONResponse(status_code=204, content=None)


class SymptomRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    user_email: str = "anonymous@pethub.local"
    session_id: str = ""


class InputHandler:
    @staticmethod
    def clean(text: str) -> str:
        normalized = re.sub(r"\s+", " ", text.strip())
        return normalized


class PromptProcessor:
    STOP_WORDS = {
        "my", "the", "is", "and", "has", "have", "pet",
        "dog", "cat", "a", "an", "with",
    }

    CANONICAL_SYMPTOMS = {
        "vomit": "vomiting",
        "vomiting": "vomiting",
        "throwing": "vomiting",
        "nausea": "vomiting",
        "fever": "fever",
        "temperature": "fever",
        "hot": "fever",
        "cough": "cough",
        "coughing": "cough",
        "breathing": "breathing",
        "breath": "breathing",
        "wheezing": "breathing",
        "diarrhea": "diarrhea",
        "loose": "diarrhea",
        "stool": "diarrhea",
        "itching": "itching",
        "itchy": "itching",
        "scratch": "itching",
        "rash": "rash",
        "skin": "rash",
        "lethargy": "lethargy",
        "tired": "lethargy",
        "weak": "lethargy",
        "blood": "blood",
        "seizure": "seizure",
        "collapse": "collapse",
        "faint": "collapse",
        "pain": "pain",
        "limping": "pain",
        "loss": "appetite_loss",
        "appetite": "appetite_loss",
        "eating": "appetite_loss",
        # Sinhala transliterations / common terms
        "kakka": "diarrhea",
        "badabada": "vomiting",
        "uwa": "itching",
        "kanna": "appetite_loss",
        "asa": "appetite_loss",
        "husma": "breathing",
        "usma": "fever",
    }

    @classmethod
    def extract_symptoms(cls, text: str) -> List[str]:
        tokens = re.findall(r"[^\W\d_]+", text.lower(), flags=re.UNICODE)
        cleaned: List[str] = []
        for token in tokens:
            if len(token) <= 2 or token in cls.STOP_WORDS:
                continue
            canonical = cls.CANONICAL_SYMPTOMS.get(token, token)
            cleaned.append(canonical)
        return sorted(set(cleaned))


class TaskPlanner:
    @staticmethod
    def plan(message: str) -> Dict[str, Any]:
        normalized = message.lower()
        wants_prediction = any(k in normalized for k in ["predict", "disease", "diagnosis", "condition"])
        return {
            "symptom_analysis": True,
            "disease_prediction": wants_prediction or len(normalized.split()) >= 3,
            "urgent_triage": any(k in normalized for k in ["blood", "seizure", "not breathing", "collapse"]),
        }


class ServiceLayer:
    def __init__(self):
        env_dsn = os.getenv("POSTGRES_DSN", "").strip()
        if env_dsn:
            self.postgres_conn_str = env_dsn
        else:
            db_name = os.getenv("POSTGRES_DB", "pethub")
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "").strip()
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")

            if db_password:
                self.postgres_conn_str = (
                    f"dbname={db_name} user={db_user} password={db_password} host={db_host} port={db_port}"
                )
            else:
                self.postgres_conn_str = f"dbname={db_name} user={db_user} host={db_host} port={db_port}"

        self.pg_enabled = True
        self.pg_warning_emitted = False
        self.pg_connect_timeout = int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "3"))
        self.neo4j_uri = os.getenv("NEO4J_URI", "")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "")

    def _pg_connect(self):
        if psycopg is None or not self.pg_enabled:
            return None
        try:
            return psycopg.connect(self.postgres_conn_str, connect_timeout=self.pg_connect_timeout)
        except Exception as ex:
            msg = str(ex)
            if "no password supplied" in msg.lower() or "fe_sendauth" in msg.lower():
                if not self.pg_warning_emitted:
                    logger.warning(
                        "PostgreSQL auth failed (password missing). Set POSTGRES_PASSWORD or POSTGRES_DSN. "
                        "Falling back to non-PostgreSQL mode for this run."
                    )
                self.pg_enabled = False
                self.pg_warning_emitted = True
                return None

            if not self.pg_warning_emitted:
                logger.warning("PostgreSQL connection failed: %s", ex)
                self.pg_warning_emitted = True
            return None

    def test_neo4j_connection(self) -> bool:
        if GraphDatabase is None or not self.neo4j_uri or not self.neo4j_password:
            return False

        driver = None
        try:
            driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            with driver.session() as session:
                session.run("RETURN 1").single()
            return True
        except Exception as ex:
            logger.warning("Neo4j connection test failed: %s", ex)
            return False
        finally:
            if driver is not None:
                driver.close()

    def fetch_postgres_care_tips(self, symptoms: List[str]) -> List[str]:
        conn = self._pg_connect()
        if conn is None:
            return []

        tips: List[str] = []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS care_tips (
                        id SERIAL PRIMARY KEY,
                        symptom VARCHAR(100) NOT NULL,
                        tip TEXT NOT NULL,
                        urgency_level VARCHAR(20) DEFAULT 'normal'
                    )
                    """
                )
                if symptoms:
                    cur.execute(
                        "SELECT tip FROM care_tips WHERE symptom = ANY(%s) LIMIT 5",
                        (symptoms,),
                    )
                    rows = cur.fetchall()
                    tips = [str(r[0]) for r in rows]
                conn.commit()
        except Exception as ex:
            logger.warning("Failed to query care_tips: %s", ex)
        finally:
            conn.close()
        return tips

    def fetch_patient_history(self, user_email: str, limit: int = 5) -> List[Dict[str, Any]]:
        conn = self._pg_connect()
        if conn is None:
            return []

        history: List[Dict[str, Any]] = []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ai_symptom_interactions (
                        id SERIAL PRIMARY KEY,
                        user_email VARCHAR(255) NOT NULL,
                        session_id VARCHAR(255) NOT NULL,
                        symptom_message TEXT NOT NULL,
                        diagnosis_suggestion TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cur.execute(
                    """
                    SELECT symptom_message, diagnosis_suggestion, created_at
                    FROM ai_symptom_interactions
                    WHERE user_email = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (user_email, limit),
                )
                for msg, diagnosis, created_at in cur.fetchall():
                    history.append(
                        {
                            "message": msg,
                            "diagnosis": diagnosis,
                            "created_at": created_at.isoformat() if created_at else None,
                        }
                    )
                conn.commit()
        except Exception as ex:
            logger.warning("Failed to query patient history: %s", ex)
        finally:
            conn.close()
        return history

    def save_interaction(self, user_email: str, session_id: str, symptom_message: str, diagnosis: str) -> None:
        conn = self._pg_connect()
        if conn is None:
            return

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ai_symptom_interactions (
                        id SERIAL PRIMARY KEY,
                        user_email VARCHAR(255) NOT NULL,
                        session_id VARCHAR(255) NOT NULL,
                        symptom_message TEXT NOT NULL,
                        diagnosis_suggestion TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cur.execute(
                    """
                    INSERT INTO ai_symptom_interactions (user_email, session_id, symptom_message, diagnosis_suggestion)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_email, session_id, symptom_message, diagnosis),
                )
                conn.commit()
        except Exception as ex:
            logger.warning("Failed to save interaction: %s", ex)
        finally:
            conn.close()

    def fetch_graph_candidates(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        if GraphDatabase is None or not self.neo4j_uri or not self.neo4j_password:
            return []

        driver = None
        rows: List[Dict[str, Any]] = []
        try:
            driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            with driver.session() as session:
                result = session.run(
                    """
                    MATCH (s:Symptom)-[:INDICATES]->(d:Disease)
                    WHERE toLower(s.name) IN $symptoms
                    RETURN d.name AS disease,
                           collect(DISTINCT s.name) AS matched,
                           count(*) AS score
                    ORDER BY score DESC
                    LIMIT 5
                    """,
                    symptoms=symptoms,
                )
                for record in result:
                    rows.append(
                        {
                            "disease": record.get("disease"),
                            "matched": record.get("matched") or [],
                            "score": int(record.get("score") or 0),
                        }
                    )
        except Exception as ex:
            logger.warning("Neo4j query failed: %s", ex)
        finally:
            if driver is not None:
                driver.close()
        return rows


class AgentDispatcher:
    @staticmethod
    def symptom_analyzer(symptoms: List[str]) -> Dict[str, Any]:
        severity = "low"
        urgent_terms = {"blood", "seizure", "collapse", "unconscious", "breathing"}
        if any(term in symptoms for term in urgent_terms):
            severity = "high"
        elif any(term in symptoms for term in {"vomiting", "fever", "diarrhea", "lethargy"}):
            severity = "medium"

        return {
            "symptoms": symptoms,
            "severity": severity,
        }

    @staticmethod
    def patient_journey_tracker(history: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "history_count": len(history),
            "recent": history,
        }

    @staticmethod
    def disease_prediction(symptoms: List[str], graph_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        if graph_candidates:
            top = graph_candidates[0]
            return {
                "diagnosis": f"Possible condition: {top['disease']}",
                "confidence": min(0.95, 0.5 + top["score"] * 0.1),
                "sources": ["neo4j-graph-db"],
            }

        symptom_set = set(symptoms)
        if not symptom_set:
            return {
                "diagnosis": "Symptoms are unclear. Please include 2 to 3 clear signs like vomiting, fever, cough, or diarrhea.",
                "confidence": 0.2,
                "sources": ["rule-engine"],
            }

        disease_profiles = [
            {
                "name": "Gastroenteritis or food intolerance",
                "required": {"vomiting"},
                "support": {"diarrhea", "appetite_loss", "fever"},
            },
            {
                "name": "Respiratory infection",
                "required": {"cough"},
                "support": {"breathing", "fever", "lethargy"},
            },
            {
                "name": "Skin allergy or dermatitis",
                "required": {"itching", "rash"},
                "support": {"lethargy"},
            },
            {
                "name": "Acute pain or injury",
                "required": {"pain"},
                "support": {"collapse", "lethargy"},
            },
        ]

        scored: List[Dict[str, Any]] = []
        for profile in disease_profiles:
            required_hit = len(profile["required"] & symptom_set)
            support_hit = len(profile["support"] & symptom_set)
            if required_hit == 0:
                continue
            score = required_hit * 2 + support_hit
            scored.append({
                "name": profile["name"],
                "score": score,
                "matched": sorted((profile["required"] | profile["support"]) & symptom_set),
            })

        if not scored:
            symptom_text = ", ".join(sorted(symptom_set)[:4])
            return {
                "diagnosis": f"Potential mild condition based on: {symptom_text}. Monitor closely and seek vet advice if symptoms continue.",
                "confidence": 0.5,
                "sources": ["rule-engine"],
            }

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[0]
        matched_text = ", ".join(top["matched"])
        confidence = min(0.9, 0.55 + top["score"] * 0.08)

        return {
            "diagnosis": f"Possible condition: {top['name']} (matched symptoms: {matched_text})",
            "confidence": confidence,
            "sources": ["rule-engine"],
        }


class LLMAdvisor:
    def __init__(self):
        self.api_key = (
            os.getenv("OPENROUTER_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        )
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        if not self.base_url and os.getenv("OPENROUTER_API_KEY", "").strip():
            self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        self.enabled = bool(self.api_key and OpenAI is not None)
        if self.enabled:
            client_kwargs: Dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            # OpenRouter requires the api-key header explicitly
            if "openrouter.ai" in self.base_url:
                client_kwargs["default_headers"] = {"HTTP-Referer": "https://pethub.local", "X-Title": "PetHub"}
            self._client: Any = OpenAI(**client_kwargs)
        else:
            self._client = None

    def improve_response(
        self,
        message: str,
        symptoms: List[str],
        severity: str,
        rule_diagnosis: str,
        rule_care_tips: List[str],
    ) -> Dict[str, Any]:
        if not self.enabled or self._client is None:
            return {}

        system_prompt = (
            "You are a veterinary triage assistant. "
            "Provide cautious, non-definitive guidance and always recommend a veterinarian for persistent or severe symptoms. "
            "Return strict JSON only (no markdown, no code fences) with keys: diagnosis_suggestion (string), "
            "care_tips (array of strings, max 6), emergency_guidance (string), urgency (low|medium|high), "
            "follow_up_questions (array of strings, max 3)."
        )
        user_payload = {
            "user_message": message,
            "extracted_symptoms": symptoms,
            "severity": severity,
            "rule_based_diagnosis": rule_diagnosis,
            "rule_based_care_tips": rule_care_tips,
        }

        try:
            # FIX: use chat.completions.create with messages= (not responses.create with input=)
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
                extra_body={"reasoning": {"enabled": True}}
            )

            text = response.choices[0].message.content or ""
            if not text:
                return {}

            # FIX: corrected regex escaping — \s* not \\s*
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                return {}

            return self._normalize_output(parsed)
        except Exception as ex:
            logger.warning("LLM enhancement failed, falling back to rules: %s", ex)
            return {}

    @staticmethod
    def _normalize_output(parsed: Dict[str, Any]) -> Dict[str, Any]:
        diagnosis = str(parsed.get("diagnosis_suggestion", "")).strip()
        emergency = str(parsed.get("emergency_guidance", "")).strip()

        tips_raw = parsed.get("care_tips", [])
        tips: List[str] = []
        if isinstance(tips_raw, list):
            tips = [str(t).strip() for t in tips_raw if str(t).strip()]

        urgency = str(parsed.get("urgency", "")).strip().lower()
        if urgency not in {"low", "medium", "high"}:
            urgency = ""

        follow_up_raw = parsed.get("follow_up_questions", [])
        follow_up_questions: List[str] = []
        if isinstance(follow_up_raw, list):
            follow_up_questions = [str(q).strip() for q in follow_up_raw if str(q).strip()]

        return {
            "diagnosis_suggestion": diagnosis,
            "care_tips": tips[:6],
            "emergency_guidance": emergency,
            "urgency": urgency,
            "follow_up_questions": follow_up_questions[:3],
        }


def severity_to_urgency(severity: str) -> str:
    lowered = (severity or "").strip().lower()
    if lowered in {"low", "medium", "high"}:
        return lowered
    return "medium"


def default_follow_up_questions(symptoms: List[str]) -> List[str]:
    questions: List[str] = []
    if len(symptoms) < 2:
        questions.append("How long have these symptoms been present?")
    if not any(s in symptoms for s in {"fever", "vomiting", "diarrhea", "cough", "breathing"}):
        questions.append("Any changes in eating, drinking, or energy level?")
    questions.append("Has your pet eaten anything unusual in the last 24 hours?")
    return list(dict.fromkeys(questions))[:3]


def build_rule_based_care_tips(symptoms: List[str], diagnosis_text: str, severity: str) -> List[str]:
    tips_map = {
        "vomiting": "Offer small sips of water and avoid heavy food for a short period.",
        "diarrhea": "Watch hydration level and stool frequency carefully.",
        "fever": "Check body temperature trend and reduce activity.",
        "cough": "Keep the pet in a dust-free and smoke-free area.",
        "breathing": "Reduce stress and get urgent vet help if breathing worsens.",
        "itching": "Avoid new shampoos or food changes until reviewed by a vet.",
        "rash": "Prevent scratching and keep the skin area clean and dry.",
        "appetite_loss": "Offer bland food in small portions and monitor intake.",
        "lethargy": "Ensure rest and monitor behavior every few hours.",
    }

    result: List[str] = []

    if severity == "high":
        result.append("This symptom pattern looks urgent. Contact an emergency vet clinic now.")
    elif severity == "medium":
        result.append("Monitor symptoms every 2 to 4 hours and keep a short log for your vet.")

    diagnosis_lower = diagnosis_text.lower()
    if "respiratory" in diagnosis_lower:
        result.append("Keep your pet in a well-ventilated area and avoid smoke, dust, and strong sprays.")
    if "gastro" in diagnosis_lower or "food intolerance" in diagnosis_lower:
        result.append("Provide a bland diet in small portions and avoid fatty treats for the next 12 to 24 hours.")
    if "skin" in diagnosis_lower or "dermatitis" in diagnosis_lower:
        result.append("Use an e-collar if needed to prevent scratching until skin irritation settles.")
    for symptom in symptoms:
        tip = tips_map.get(symptom)
        if tip:
            result.append(tip)
        else:
            result.append(f"Track changes related to '{symptom}' and share them with your veterinarian.")

    if not result:
        result = [
            "Keep your pet hydrated with small amounts of water.",
            "Observe appetite, energy level, and temperature changes.",
            "Avoid giving human medicine unless a vet approves it.",
        ]

    deduped = list(dict.fromkeys(result))
    return deduped[:6]


def build_final_care_tips(
    symptoms: List[str],
    diagnosis_text: str,
    severity: str,
    postgres_tips: List[str],
) -> List[str]:
    base = build_rule_based_care_tips(symptoms, diagnosis_text, severity)

    combined: List[str] = []
    for tip in base + postgres_tips:
        cleaned = str(tip).strip()
        if cleaned and cleaned not in combined:
            combined.append(cleaned)

    return combined[:6]


# FIX: initialize after env vars are loaded (dotenv runs above at module level)
SERVICE_LAYER = ServiceLayer()
LLM_ADVISOR = LLMAdvisor()


@app.post("/orchestrate/symptom")
async def orchestrate_symptom(request: SymptomRequest):
    cleaned_message = InputHandler.clean(request.message)
    symptoms = PromptProcessor.extract_symptoms(cleaned_message)
    plan = TaskPlanner.plan(cleaned_message)

    symptom_result = AgentDispatcher.symptom_analyzer(symptoms)
    history = SERVICE_LAYER.fetch_patient_history(request.user_email)
    journey_result = AgentDispatcher.patient_journey_tracker(history)
    graph_candidates = SERVICE_LAYER.fetch_graph_candidates(symptoms)
    prediction = AgentDispatcher.disease_prediction(symptoms, graph_candidates)

    diagnosis_suggestion = prediction["diagnosis"]
    postgres_tips = SERVICE_LAYER.fetch_postgres_care_tips(symptoms)
    care_tips = build_final_care_tips(
        symptoms=symptoms,
        diagnosis_text=diagnosis_suggestion,
        severity=symptom_result["severity"],
        postgres_tips=postgres_tips,
    )

    emergency_guidance = "Visit the nearest veterinary clinic immediately."
    if symptom_result["severity"] != "high":
        emergency_guidance = "If symptoms continue for more than 24 hours, consult a veterinarian."
    urgency = severity_to_urgency(symptom_result["severity"])
    follow_up_questions = default_follow_up_questions(symptoms)

    llm_result = LLM_ADVISOR.improve_response(
        message=cleaned_message,
        symptoms=symptoms,
        severity=symptom_result["severity"],
        rule_diagnosis=diagnosis_suggestion,
        rule_care_tips=care_tips,
    )
    if llm_result.get("diagnosis_suggestion"):
        diagnosis_suggestion = llm_result["diagnosis_suggestion"]
    if llm_result.get("care_tips"):
        care_tips = build_final_care_tips(
            symptoms=symptoms,
            diagnosis_text=diagnosis_suggestion,
            severity=symptom_result["severity"],
            postgres_tips=llm_result.get("care_tips", []),
        )
    if llm_result.get("emergency_guidance"):
        emergency_guidance = llm_result["emergency_guidance"]
    if llm_result.get("urgency"):
        urgency = llm_result["urgency"]
    if llm_result.get("follow_up_questions"):
        follow_up_questions = llm_result["follow_up_questions"]

    # FIX: use timezone-aware datetime (utcnow() is deprecated in Python 3.12+)
    SERVICE_LAYER.save_interaction(
        request.user_email,
        request.session_id or f"session-{int(datetime.now(timezone.utc).timestamp())}",
        cleaned_message,
        diagnosis_suggestion,
    )

    return {
        "session_id": request.session_id,
        "diagnosis_suggestion": diagnosis_suggestion,
        "care_tips": care_tips,
        "emergency_guidance": emergency_guidance,
        "urgency": urgency,
        "follow_up_questions": follow_up_questions,
        "confidence": prediction["confidence"],
        "sources": prediction["sources"] + (["openai"] if llm_result else []),
        "pipeline": {
            "input_handler": "done",
            "prompt_processor": {
                "symptoms": symptoms,
            },
            "task_planner": plan,
            "agent_dispatcher": {
                "symptom_analyzer": symptom_result,
                "patient_journey_tracker": {
                    "history_count": journey_result["history_count"],
                },
                "disease_prediction": prediction,
            },
            "service_layer": {
                "neo4j_matches": graph_candidates,
                "postgres_tips_used": len(postgres_tips),
            },
            "llm": {
                "provider": "openai" if llm_result else "rule-engine-only",
                "enabled": LLM_ADVISOR.enabled,
                "structured_output": True,
            },
        },
    }


@app.get("/admin/orchestrator/status")
async def orchestrator_status():
    conn = SERVICE_LAYER._pg_connect()
    postgres_ready = conn is not None
    if conn:
        conn.close()

    neo4j_ready = SERVICE_LAYER.test_neo4j_connection()
    return {
        "status": "ok",
        "postgres_ready": postgres_ready,
        "neo4j_ready": neo4j_ready,
        "openai_configured": LLM_ADVISOR.enabled,
        "neo4j_configured": bool(SERVICE_LAYER.neo4j_uri and SERVICE_LAYER.neo4j_password and GraphDatabase is not None),
        "postgres_configured": bool(SERVICE_LAYER.postgres_conn_str),
    }


@app.post("/verify-pet-image")
async def verify_pet_image(file: UploadFile = File(...)):
    """
    Upload an image file and check if a cat or dog is detected.
    Returns {"is_valid": bool, "message": str}
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        global model
        if model is None:
            try:
                model = YOLO("yolov8n.pt")
                logger.info("YOLOv8 model loaded on-demand for image verification.")
            except Exception as ex:
                raise HTTPException(status_code=503, detail=f"Model is unavailable: {str(ex)}")

        results = model.predict(source=image, conf=0.5, save=False)

        detected_classes = []
        for result in results:
            if result.boxes is not None and result.boxes.cls is not None:
                classes = result.boxes.cls.cpu().numpy().tolist()
                detected_classes.extend([int(c) for c in classes])

        has_pet = any(cls in ALLOWED_CLASSES for cls in detected_classes)

        if has_pet:
            return JSONResponse({
                "is_valid": True,
                "message": "Valid pet photo. Cat or dog detected."
            })
        else:
            return JSONResponse({
                "is_valid": False,
                "message": "Invalid photo. No cat or dog detected."
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing image: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


@app.get("/health")
async def health_check():
    """Simple healthcheck endpoint."""
    return {"status": "ok"}