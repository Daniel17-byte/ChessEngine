# ⚡ NEXT.JS ROUTER FIX - Required Manual Steps

## 🔴 Problem
Next.js error: "App Router and Pages Router both match path: /"

## ✅ Solution

### Step 1: Remove Pages Router Folder
Delete the entire `src/pages/` folder from your project:

```bash
rm -rf src/pages/
```

**Files to be deleted:**
- `src/pages/index.tsx`
- `src/pages/login.tsx`
- `src/pages/register.tsx`
- `src/pages/play.tsx`
- `src/pages/leaderboard.tsx`
- `src/pages/profile.tsx`

### Step 2: Clean Build Cache
```bash
# Remove Next.js build cache
rm -rf .next/

# Clean install
npm install
```

### Step 3: Restart Development Server
```bash
npm run dev
```

## 📁 New App Router Structure
All pages are now in `src/app/`:

```
src/app/
├── layout.tsx              # Root layout with AuthProvider
├── page.tsx               # Home (auth redirect)
├── globals.css            # Global styles
├── login/
│   └── page.tsx          # Login page
├── register/
│   └── page.tsx          # Register page
├── play/
│   └── page.tsx          # Chess game page
├── leaderboard/
│   └── page.tsx          # Leaderboard page
└── profile/
    └── page.tsx          # Profile page
```

## 🎯 Routes Available
- `/` - Home (redirects to /login or /play based on auth)
- `/login` - Login page
- `/register` - Register page
- `/play` - Chess game (protected)
- `/leaderboard` - Leaderboard (protected)
- `/profile` - User profile (protected)

## ✨ Why This Works
- **App Router (src/app/)**: Modern Next.js 13+ routing
- **Single Entry Point**: One `/` that handles redirects
- **No Conflicts**: Only App Router is active
- **Type Safety**: Full TypeScript support with proper imports

## 🚀 After Setup
The application should work perfectly with:
- ✅ Authentication system
- ✅ Protected routes
- ✅ Board flip functionality
- ✅ New game dialog
- ✅ Leaderboard
- ✅ Profile stats

---

**Once you delete src/pages/, the error will be resolved and dev server will start normally!** 🎉

