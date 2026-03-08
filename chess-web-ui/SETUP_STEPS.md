# 🔧 STEP-BY-STEP SETUP INSTRUCTIONS

## ⚠️ IMPORTANT: Fix Router Conflict First!

Your Next.js project has both App Router (`src/app/`) and Pages Router (`src/pages/`) which causes a conflict. **You MUST delete `src/pages/` folder.**

---

## 📝 Step 1: Delete src/pages/ Folder

### On macOS/Linux:
```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/chess-web-ui
rm -rf src/pages/
rm -rf .next/
```

### On Windows (PowerShell):
```powershell
cd C:\Users\...\chess-web-ui
Remove-Item -Recurse -Force src/pages/
Remove-Item -Recurse -Force .next/
```

---

## 📋 Step 2: Verify File Structure

After deletion, your `src/` folder should look like:
```
src/
├── app/                    ✅ (contains pages)
├── components/             ✅ (Layout, ChessBoard, etc.)
├── context/               ✅ (AuthContext, ChessContext)
├── api/                   ✅ (authApi, statsApi, etc.)
└── styles/                ✅ (CSS modules)

❌ src/pages/ should NOT exist
```

---

## 🔄 Step 3: Clean Install

```bash
cd chess-web-ui

# Remove node_modules and lock file
rm -rf node_modules/
rm package-lock.json

# Reinstall
npm install
```

---

## 🚀 Step 4: Start Development Server

```bash
npm run dev
```

You should see:
```
> next dev --turbopack
  ▲ Next.js 15.3.4
  ▲ using Turbopack

Ready in XXXms

Local:        http://localhost:3000
```

---

## ✅ Step 5: Open in Browser

Open: **http://localhost:3000**

You should see:
- Blank white page (loading)
- Then redirect to `/login` (if not authenticated)

---

## 🎮 Step 6: Test the Application

### Register
1. You should be on `/login` page
2. Click "Register here" link
3. Fill in:
   - Username: `testuser`
   - Email: `test@example.com`
   - Password: `password123`
   - Confirm: `password123`
4. Click "Register"
5. Should redirect to `/play` page

### Play Chess
1. Should see chess board
2. Click "🎮 New Game" button
3. Select color and opponent
4. Click "▶️ Start Game"
5. Can flip board with "🔄 Flip Board"

### Check Stats
1. Click "🏆 Leaderboard" in navbar (top right)
2. Should see empty leaderboard (no games yet)
3. Click "👤 Profile"
4. Should see "No statistics yet"

---

## 🔌 Make Sure Backend Services Are Running

Before testing, ensure these are running:

### Terminal 1: Flask AI Engine
```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
python3 app.py
```
Should show:
```
WARNING in app.run()
 * Running on http://127.0.0.1:5000
```

### Terminal 2: Java Backend (if needed)
Verify these services are up:
- users-be on port 8080
- stats-be on port 8080
- game-be on port 8080
- matchmaking-be on port 8080

### Terminal 3: Next.js Frontend
```bash
cd chess-web-ui
npm run dev
```

---

## 🐛 Debugging

### Error: "Cannot find module '../context/AuthContext'"
- Clear cache: `rm -rf .next/`
- Restart IDE (VS Code)
- Restart dev server

### Error: "Port 3000 already in use"
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
npm run dev
```

### Error: "Login failed"
1. Check if users-be is running (port 8080)
2. Open browser DevTools (F12)
3. Check Network tab for API calls
4. Check Console for CORS errors

### Error: "Chess board not loading"
1. Check if ai-engine is running (port 5000)
2. Open browser DevTools
3. Check Network tab for `/api/game/get_board` call
4. Check API response

---

## ✨ Expected Behavior

| Page | Authentication | Behavior |
|------|---|---|
| `/` | Not logged in | Redirects to `/login` |
| `/` | Logged in | Redirects to `/play` |
| `/login` | Any | Show login form |
| `/register` | Any | Show register form |
| `/play` | Not logged in | Redirects to `/login` |
| `/play` | Logged in | Show chess board |
| `/leaderboard` | Not logged in | Redirects to `/login` |
| `/leaderboard` | Logged in | Show leaderboard |
| `/profile` | Not logged in | Redirects to `/login` |
| `/profile` | Logged in | Show profile with stats |

---

## 📚 File Locations

Important files created:

```
chess-web-ui/
├── src/app/
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home (/)
│   ├── globals.css              # Global styles
│   ├── login/page.tsx           # Login page
│   ├── register/page.tsx        # Register page
│   ├── play/page.tsx            # Chess game
│   ├── leaderboard/page.tsx     # Leaderboard
│   └── profile/page.tsx         # Profile
├── src/context/
│   ├── AuthContext.tsx          # Auth state
│   └── ChessContext.tsx         # Chess state
├── src/api/
│   ├── authApi.ts               # Auth API
│   ├── statsApi.ts              # Stats API
│   ├── matchmakingApi.ts        # Matchmaking API
│   └── chessApi.ts              # Chess API
└── src/components/
    ├── Layout.tsx               # Main layout
    ├── ChessBoard.tsx           # Chess board
    ├── NewGameDialog.tsx        # New game dialog
    ├── ProtectedRoute.tsx       # Auth guard
    └── *.module.css             # Styles
```

---

## 🎯 Checklist

- [ ] Deleted `src/pages/` folder
- [ ] Deleted `.next/` folder
- [ ] Ran `npm install`
- [ ] Running `npm run dev` shows no errors
- [ ] Can open http://localhost:3000
- [ ] Redirected to `/login`
- [ ] Can navigate to `/register`
- [ ] Can create account
- [ ] Can login
- [ ] Can see chess board on `/play`
- [ ] Can see leaderboard on `/leaderboard`
- [ ] Can see profile on `/profile`
- [ ] Can flip board
- [ ] Can start new game

---

## 🚨 If Still Having Issues

1. **Check that src/pages/ is DELETED**
   ```bash
   ls -la src/pages/
   # Should say "No such file or directory"
   ```

2. **Verify app/ structure**
   ```bash
   ls -la src/app/
   # Should have: layout.tsx, page.tsx, globals.css, login/, register/, play/, leaderboard/, profile/
   ```

3. **Restart everything**
   ```bash
   # Kill all Node processes
   pkill -f "node"
   pkill -f "next dev"
   
   # Clear caches
   rm -rf .next/
   rm -rf node_modules/
   
   # Clean install
   npm install
   npm run dev
   ```

---

## 💡 Tips

- Use `npm run build` to check for errors before running in production
- Use `npm run lint` to find code issues
- Open DevTools (F12) to debug API calls and errors
- Check browser Console for JavaScript errors
- Check Network tab for failed API calls

---

**You're all set! 🎉 Enjoy your Chess Engine!**

