# 🚀 Deploy to Railway - Quick Guide

## Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - MedSupport System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/medsupport-system.git
git push -u origin main
```

## Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect Python and deploy

## Step 3: Get Your Live URL
- Railway will give you a URL like: `https://your-app-name.railway.app`
- Add this to your portfolio as "Live Demo"

## Step 4: Update Portfolio
Add this to your portfolio:
```html
<a href="https://your-app-name.railway.app" target="_blank" class="btn btn-primary">
    <i class="fas fa-external-link-alt"></i> Live Demo
</a>
```

## Demo Credentials:
- **Admin**: admin / admin123
- **Technician**: tech / tech123  
- **User**: user / user123 