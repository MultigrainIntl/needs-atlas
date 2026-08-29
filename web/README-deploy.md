# Deploying the Needs Atlas secure site (Firebase Hosting + Auth)

The site lives in `web/`. It shows a login screen (Firebase Email/Password), and
after sign-in renders the live dashboard from `web/counties.json` and
`web/tracts_need.csv` — the same data the assessment documents are built from.
Those two data files are refreshed automatically by the **Build Atlas data**
GitHub Action, so a fresh clone already has them.

Until you add a Firebase config the site runs in **demo mode**: a click-through
gate so you can open it locally with no setup.

## One-time setup

1. **Install the CLI** (needs Node.js):

       npm install -g firebase-tools

2. **Create a Firebase project** at https://console.firebase.google.com
   (e.g. name it `needs-atlas`). Free "Spark" plan is enough for Hosting + Auth.

3. **Enable sign-in:** in the console, Build - Authentication - Sign-in method -
   enable **Email/Password**. Leave sign-up closed; you add each Zufall user by
   hand under Authentication - Users - Add user. (No one can self-register.)

4. **Register a web app:** Project settings - General - Your apps - Web (`</>`).
   Copy the `firebaseConfig` object it gives you.

5. **Paste that config** into `web/index.html`, into the `FIREBASE_CONFIG = { }`
   block near the top of the `<script type="module">` (around line 125). Once it
   is non-empty the login screen switches from demo to real authentication.

6. **Point the CLI at your project:** edit `.firebaserc` and replace
   `REPLACE_WITH_YOUR_FIREBASE_PROJECT_ID` with your project id (shown in the
   console URL and in Project settings).

## Deploy

    firebase login          # once, in a browser
    firebase deploy --only hosting

The CLI prints your live URL (e.g. `https://needs-atlas.web.app`). Re-run
`firebase deploy --only hosting` any time to push a new version. To refresh the
data first, run the GitHub Action (or `git pull` a clone that has) so the latest
`web/counties.json` and `web/tracts_need.csv` are in place.

## Optional: embed the ArcGIS temporal heat map

In `web/index.html` set `ARCGIS_EMBED_URL` to your published ArcGIS Online
time-enabled web-map / dashboard URL. The placeholder panel is replaced by the
live map (with its year slider) automatically.

## Security note — read before V2

V1 data is **public U.S. Census (ACS) information**, so serving it as static
files behind a staff login is appropriate: the login keeps the tool tidy and
staff-only, and nothing sensitive is exposed even to someone who finds a file
URL directly.

When Zufall's **own patient / utilization data** is layered in (V2), do **not**
host it as static files. Move it into **Cloud Firestore** (or Cloud Storage)
with a security rule such as `allow read: if request.auth != null;`, or serve it
through a **Cloud Function** that checks the caller's auth. Firebase Hosting is a
public CDN; only Firestore/Storage/Functions can actually gate data by sign-in.
