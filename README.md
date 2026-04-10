# PetHub Fullstack Application

This repository contains a Spring Boot backend and an Expo React Native frontend for a simple pet management app. Users can register, login, view a list of pets, and upload new pets with images.

It now also includes an agentic AI symptom analysis flow:
- User symptom message in Expo app
- Spring Boot API bridge + PostgreSQL logging
- FastAPI orchestrator pipeline
- Neo4j + PostgreSQL data connectors

## Backend (Spring Boot)

1. Open a terminal in `PetHub/PetHub`.
2. Build and run the server:
   ```powershell
   cd PetHub\PetHub
   .\mvnw.cmd spring-boot:run
   ```
   *or* if you have Maven installed:
   ```powershell
   mvn spring-boot:run
   ```
3. The API will start on port `8080`. Endpoints:
   - `POST /auth/register` – register new user
   - `POST /auth/login` – login
   - `GET /pets` – list all pets
   - `GET /pets/{id}` – pet details
   - `POST /pets/upload` – add pet with image
   - `GET /pets/image/{id}` – serve pet image
   - `POST /agent/chat` – send symptom text to orchestrator
   - `GET /agent/admin/queries` – latest symptom requests (admin monitor)

> ⚠️ When running on a device/emulator, make sure the frontend's `BASE_URL` matches the host machine. See frontend instructions below.


## Frontend (Expo React Native)

1. Navigate to the Expo app directory:
   ```powershell
   cd FrontEnd\pethub_expo
   npm install           # or yarn
   ```
2. Start the development server:
   ```powershell
   npm start
   # expo start
   ```
   Then open on emulator or physical device.

3. **Configure network access**
   - iOS Simulator / Web: `BASE_URL = 'http://localhost:8080'` (default)
   - Android Emulator: `BASE_URL = 'http://10.0.2.2:8080'`
   - Physical device: replace with your computer's LAN IP, e.g. `http://192.168.1.100:8080`.

   Update the constant at `services/api.js` if necessary.

4. Use the app:
   - Register a new account via **Sign Up**.
   - After registering, login with the same credentials.
   - Upon success the app navigates to the pet list screen.
   - The initial pet list is seeded automatically if empty.
   - Add pets using the **+ Add Pet** button; images are uploaded to the backend.
   - Open **Symptom Agent** from the home screen to submit symptoms.
   - Open **Admin Monitor** from the home screen to view recent symptom requests.

5. Logout using the button at the bottom of the list. Authentication state is saved to AsyncStorage, so closing and reopening the app will keep you logged in. If you ever see the login screen unexpectedly, check the Metro logs for error messages (we added extra console logs to `AuthContext.jsx` and `api.js` to help debugging).


## Troubleshooting

- **Login screen stuck:**
  - Make sure the backend is running and reachable from the device.
  - Look at Expo logs for `loginAPI response:` and `Restored user from storage:` messages.
  - Confirm that `AsyncStorage` contains a valid `user` entry (clear storage to test fresh behaviour).

- **Network errors when fetching pets:**
  - Verify `BASE_URL` is correct for your environment.
  - Check backend console for incoming requests.

- **Symptom Agent returns orchestrator unavailable:**
  - Make sure the FastAPI service in `PetImageChecker` is running on port `8000`.


## FastAPI Orchestrator (PetImageChecker)

1. Start the service:
   ```powershell
   cd PetImageChecker
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Agent orchestration endpoint:
   - `POST /orchestrate/symptom`

3. Optional DB environment variables:
   - `POSTGRES_DSN` (example: `dbname=pethub user=postgres password=your_password host=localhost port=5432`)
   - `NEO4J_URI` (example: `bolt://localhost:7687`)
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`
   - `OPENROUTER_API_KEY` (optional, preferred for OpenRouter models)
   - `OPENAI_API_KEY` (optional fallback key)
   - `OPENAI_BASE_URL` (optional endpoint URL, auto-set to OpenRouter URL when `OPENROUTER_API_KEY` is present)
   - `OPENAI_MODEL` (optional, default: `gpt-4.1-mini`)

- **Layout warning:**
  - The layout has been updated to avoid
    `Layout children must be of type Screen` warnings; a `splash.jsx` file was added and is shown while the app restores authentication.


   ## Vaccination Card Verification Roadmap

   The current backend verifier only checks pet photos. If you want to add vaccination card or certificate verification, the recommended flow is:

   1. User uploads a JPG/PNG vaccination card image.
   2. The backend sends the image to an OCR layer to extract text fields such as pet name, vaccine type, date, and vet name.
   3. The extracted data is parsed with validation rules and database checks.
   4. The app marks the record as verified only if the card passes the checks.

   Practical validation options:

   - Rule checks for future dates, invalid vaccine names, and missing fields.
   - Database matching for pet records and verified vet or clinic names.
   - Duplicate-image and metadata checks to catch reused or edited uploads.
   - QR or serial-code verification for the most reliable validation path.

   Recommended stack for that feature:

   - Frontend: image picker and upload preview in Expo or React Native.
   - Backend: Spring Boot upload endpoint plus validation orchestration.
   - OCR: Google ML Kit or Tesseract.
   - Fake-detection support: OpenCV or a small TensorFlow model.

   This can be added later as a separate vaccination verification flow without changing the existing pet-photo upload path.



Feel free to explore and modify! If you run into problems, the source code is instrumented with console logs; check the developer console where Metro/Expo prints information.



User: i want to add this.upadte this 
Short answer 👉 Yes, karanna puluwan, but you need combination of Image Processing + AI + Validation logic.

මම simple Sinhala + English mix එකෙන් explain කරන්නම් 👇

🔥 Problem eka breakdown karamu

ඔයාට ඕනේ:

User vaccination card / certificate image upload කරනවා
App එක:
Image eka read කරලා details extract කරනවා
Real vaccination ekak da check කරනවා
Valid නම් → mark as ✅ Vaccinated
Fake / wrong නම් → ❌ Reject කරනවා
🧠 Solution Architecture (Step by Step)
✅ Step 1: Image Upload
User upload කරනවා (JPG/PNG)
Backend (Spring Boot) එකට send කරනවා
✅ Step 2: OCR (Text extract karanna)

Image ekin text ganna one 👉 use:

Google ML Kit / Tesseract OCR

Example extract:

Pet Name: Bruno
Vaccine: Rabies
Date: 2025-03-10
Doctor: Dr. Silva
✅ Step 3: Important Fields Identify karanna

Extract karapu text eken parse karanna:

Pet Name
Vaccine Type (Rabies, DHPP etc.)
Date
Vet Name / Hospital

👉 Regex / NLP use karanna puluwan

✅ Step 4: Validation Logic (VERY IMPORTANT 🔥)

Fake detect karanna main logic eka meka 👇

✔️ Method 1: Rule-based validation

Check karanna:

Date future ekak da? ❌
Vaccine name valid list ekak athulathda? ✅
Pet name match wenawada DB ekata? ✅
✔️ Method 2: Database Matching
Vet clinics / doctors list ekak maintain karanna
OCR eken gaththa doctor name match karanna
✔️ Method 3: Image Authenticity Check (Fake detect)

Use:

Image metadata check
Duplicate image detection
AI model (CNN) for fake documents

👉 example:

Photoshop edit karapu eka detect karanna
Same image multiple users upload karanawada check karanna
✔️ Method 4 (Advanced 🔥🔥): QR Code / Serial Verification

Best method 👇

Vet clinics walata QR code / ID system ekak denawa
Image eke QR code thiyanawada check karanna
Scan karala backend eke verify karanna

👉 This is MOST reliable

🏗️ Tech Stack Recommendation
Frontend (Android / React Native)
Image picker
Preview + upload
Backend (Spring Boot)
Image processing API
OCR integration
Validation logic
AI / ML
OCR: Google ML Kit / Tesseract
Fake detection: TensorFlow Lite / OpenCV
Database
Pets
Vaccination records
Verified vets
🔄 Flow eka (Simple)
Upload Image
     ↓
OCR (text extract)
     ↓
Parse data
     ↓
Validation checks
     ↓
IF valid → Vaccinated ✅
ELSE → Fake ❌
⚠️ Important Reality Check

💡 100% fake detect karanna hard (even big companies struggle)

👉 But you can make it:

70–90% accurate using:
OCR + rules
Vet DB
QR system (best)
💡 Smart Idea (Highly Recommended 🔥)

Instead of only image checking:

👉 Add “Verified Vet Upload System”

Vet login account
Vet directly upload vaccination record
Auto verified ✅

User upload = secondary method

🚀 Bonus Feature Ideas (ඔයාගේ app එක level up වෙනවා)
Vaccine expiry reminder 🔔
Next dose prediction 📅
Health timeline chart 📊
Disease prevention tips
👉 Summary

✔️ Puluwan
✔️ Use OCR + validation
✔️ Add AI for fake detection
✔️ Best = QR / Vet verification system

GitHub Copilot: Optimizing tool selection...I’m checking the project notes and code layout first so I can place this in the right part of the app and make the change at the source instead of guessing.

Searched for regex `vaccin|vaccine|vaccination|certificate|ocr|qr|verify|verified` (`**/PetHub/PetHub/src/**`), 2 results

Searched for files matching `**/PetHub/PetHub/src/main/java/**/*.java`, 11 matches

Searched for files matching `**/FrontEnd/pethub_expo/app/**/*.jsx`, 15 matches

Read memory [](file:///c%3A/Users/Anupa/AppData/Roaming/Code/User/workspaceStorage/deba06803b9ffe760cc7774ea9feb4e0/GitHub.copilot-chat/memory-tool/memories/repo/pethub2-notes.md)

I found an existing image-verification hook in the backend, so I’m reading that path and the Python checker together to see whether this is a documentation update or a real feature gap.

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetHub/PetHub/src/main/java/com/anupa/PetHub/controller/PetController.java)

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetImageChecker/main.py#1-1), lines 1 to 260

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/FrontEnd/pethub_expo/app/add-pet.jsx)

The current backend already calls a Python verifier for pet photos, so I’m checking whether the supporting API exists and whether the frontend is wired for uploads before I change behavior.

Searched for regex `verify-pet-image|vaccin|uploadPet|updatePet|imagePath` (`**/*.{js,jsx,java,py,ts,tsx}`), 29 results

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/FrontEnd/pethub_expo/services/api.js)

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetHub/PetHub/src/main/java/com/anupa/PetHub/model/Pet.java)

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetHub/PetHub/pom.xml)

I’ve confirmed the current implementation is pet-photo verification, not vaccination-card verification, so I’m checking the project docs next to see whether this belongs in a feature spec or a code path.

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetHub/PetHub/src/main/java/com/anupa/PetHub/PetHubApplication.java)

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/README.md)

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/CHATBOT_FIX_GUIDE.md)

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetImageChecker/README.md)

I’m making a docs-only update that captures the vaccination-card verification idea without pretending it’s already implemented, and I’ll anchor it in the AI service docs where the image verification already lives.

Apply Patch

The first patch failed on tool formatting, so I’m reapplying the same docs update with the required patch metadata.

Generating patch (37 lines) in [](file:///c%3A/Users/Anupa/Desktop/PetHub2/README.md)


```

```
I’ve added the roadmap to the main README; I’m also aligning the FastAPI service docs so the current `/verify-pet-image` endpoint is clearly distinguished from the future vaccination-card flow.

Generating patch (12 lines) in [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetImageChecker/README.md)


```

```
I’m recording the verified service scope so the next change doesn’t accidentally treat the pet-photo verifier as a vaccination-card checker.

Inserted into memory file [](file:///c%3A/Users/Anupa/AppData/Roaming/Code/User/workspaceStorage/deba06803b9ffe760cc7774ea9feb4e0/GitHub.copilot-chat/memory-tool/memories/repo/pethub2-notes.md)

The memory insert point was off by one, so I’m appending it at the end instead.

Inserted into memory file [](file:///c%3A/Users/Anupa/AppData/Roaming/Code/User/workspaceStorage/deba06803b9ffe760cc7774ea9feb4e0/GitHub.copilot-chat/memory-tool/memories/repo/pethub2-notes.md)

The docs and memory update are in place; I’m grabbing the exact line numbers now so I can point you to the new section cleanly.

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/README.md#55-55), lines 55 to 120

Read [](file:///c%3A/Users/Anupa/Desktop/PetHub2/PetImageChecker/README.md#1-1), lines 1 to 80

I’ve confirmed the content, and I’m pulling exact match locations now so I can reference the new section precisely instead of approximating.

Searched for text `Vaccination Card Verification Roadmap` (`**/README.md`), 1 result

Searched for text `Current scope:` (`**/PetImageChecker/README.md`), 1 result

I added a vaccination-card verification roadmap to README.md and clarified in README.md that the current `/verify-pet-image` endpoint only handles pet photos, not vaccination cards yet.

The docs now describe the intended OCR + validation flow, including rule checks, vet/database matching, duplicate-image checks, and QR/serial verification as the stronger option. If you want, I can implement the actual upload/verification flow next.

Made changes.

User: can you do Vaccination Card Verification Roadmap eka mage system ekata gelapena vidiyata karanna puluwnda.ui eke cat da dog da kiyala select karanna ahaala ita passe dognam main vaccin tika show karanna one dog ta adaalawa.eta passe e ekin ekata adaalwa userta upload karanna puluwn wenna ona image ekak.it passe e image eka system eka valied image ekakda nedda kiyala verify karagena respond karnanna ona.do it 
