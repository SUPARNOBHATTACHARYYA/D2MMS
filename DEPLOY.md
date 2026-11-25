# Deploying the Course Portal to GitHub Pages

This website is a static scientific computing portal authored in Quarto and built with vanilla Web standards (HTML5 Canvas, KaTeX math typesetting, and Lora typography). The site builds directly into the `docs/` folder and is designed for hosting on **GitHub Pages**.

---

## 1. Quick Deploy: From `/docs` Folder (Recommended)

GitHub Pages natively supports hosting directly from the `/docs` folder of your `main` branch.

### Step 1: Push workspace to GitHub
```powershell
git init
git add .
git commit -m "Deploy vibrations and dynamic modeling lecture website"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### Step 2: Enable GitHub Pages in Repository Settings
1. In your GitHub repository, go to **Settings** $\to$ **Pages**.
2. Under **Build and deployment** $\to$ **Source**, select **Deploy from a branch**.
3. Under **Branch**, select `main` and choose the `/docs` folder from the dropdown.
4. Click **Save**.
5. Your website will be live at:
   `https://<your-username>.github.io/<your-repo-name>/`

---

## 2. Alternate: Automated Deployment via GitHub Actions

If you prefer GitHub to automatically build the site from source on every push, the included workflow at [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) will handle it:
1. Go to **Settings** $\to$ **Pages**.
2. Under **Build and deployment** $\to$ **Source**, choose **GitHub Actions**.
3. Every push to `main` will build and deploy the `docs` folder automatically.

---

## 3. Local Preview & Development

To test and build locally on your machine before pushing to GitHub:

```powershell
# Build static site into docs/
.\make.ps1 build

# Serve docs/ locally on http://127.0.0.1:8080
.\make.ps1 serve

# Live-reload development preview
.\make.ps1 preview
```
