# 🚀 Deploy to Render - Alternative Guide

## Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - MedSupport System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/medsupport-system.git
git push -u origin main
```

## Step 2: Deploy on Render
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: medsupport-system
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

## Step 3: Get Your Live URL
- Render will give you a URL like: `https://your-app-name.onrender.com`
- Add this to your portfolio as "Live Demo"

## Step 4: Update Portfolio
Add this to your portfolio:
```html
<a href="https://your-app-name.onrender.com" target="_blank" class="btn btn-primary">
    <i class="fas fa-external-link-alt"></i> Live Demo
</a>
```

## Demo Credentials:
- **Admin**: admin / admin123
- **Technician**: tech / tech123  
- **User**: user / user123 