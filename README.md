# PetHub Fullstack Application

This repository contains a Spring Boot backend and an Expo React Native frontend for a simple pet management app. Users can register, login, view a list of pets, and upload new pets with images.

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

5. Logout using the button at the bottom of the list. Authentication state is saved to AsyncStorage, so closing and reopening the app will keep you logged in. If you ever see the login screen unexpectedly, check the Metro logs for error messages (we added extra console logs to `AuthContext.jsx` and `api.js` to help debugging).


## Troubleshooting

- **Login screen stuck:**
  - Make sure the backend is running and reachable from the device.
  - Look at Expo logs for `loginAPI response:` and `Restored user from storage:` messages.
  - Confirm that `AsyncStorage` contains a valid `user` entry (clear storage to test fresh behaviour).

- **Network errors when fetching pets:**
  - Verify `BASE_URL` is correct for your environment.
  - Check backend console for incoming requests.

- **Layout warning:**
  - The layout has been updated to avoid
    `Layout children must be of type Screen` warnings; a `splash.jsx` file was added and is shown while the app restores authentication.


## Project Structure

- `PetHub/PetHub` – backend Spring Boot application
- `FrontEnd/pethub_expo` – Expo frontend (React Native)
  - `app/` – expo-router pages and layouts
  - `components/`, `hooks/`, `context/`, `services/` etc.


Feel free to explore and modify! If you run into problems, the source code is instrumented with console logs; check the developer console where Metro/Expo prints information.
