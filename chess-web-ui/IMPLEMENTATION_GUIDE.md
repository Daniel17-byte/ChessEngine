# Chess Engine - Full Stack Web Application

## 🎯 Features Implemented

### ✅ Phase 1: Board UI Enhancements
- **Board Flip**: Toggle button to invert the board (rotate 180°)
- **New Game Dialog**: Modal to select:
  - Player color (White/Black)
  - Opponent type (AI/Player - Player coming soon)
  - Game resets with settings
- **Game Status Display**: Shows current game type, color, and game-over state

### ✅ Phase 2: Authentication System
- **User Registration**: Email, username, password with validation
- **User Login**: Secure login with session management
- **Protected Routes**: Pages require authentication
- **Session Persistence**: User stays logged in across page reloads

### ✅ Phase 3: Player Stats & Leaderboard
- **Leaderboard Page**: 
  - Sorted by win rate and wins
  - Medal badges for top 3 (🥇🥈🥉)
  - Displays: Rank, Player, Wins, Losses, Draws, Total Games, Win Rate
- **Profile Page**:
  - User information display
  - Personal statistics
  - Win rate visualization

### ✅ Phase 4: Navigation & UI
- **Layout Component**:
  - Responsive navbar with mobile menu
  - User menu with logout
  - Footer
- **Responsive Design**: Mobile-friendly across all pages

### ✅ Phase 5: API Integration
- **Auth API**: register, login, get users
- **Stats API**: record wins/losses/draws, get player/leaderboard stats
- **Matchmaking API**: create matches, join matches, list matches
- **Chess API**: board state, make moves (integrated)

## 📁 Project Structure

```
chess-web-ui/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with AuthProvider
│   │   ├── page.tsx            # Auth redirect page
│   │   └── globals.css         # Global styles
│   ├── pages/
│   │   ├── index.tsx           # Home (redirects to /play)
│   │   ├── play.tsx            # Chess game page
│   │   ├── login.tsx           # Login page
│   │   ├── register.tsx        # Register page
│   │   ├── leaderboard.tsx     # Leaderboard page
│   │   └── profile.tsx         # Profile page
│   ├── components/
│   │   ├── Layout.tsx          # Main layout with navbar
│   │   ├── ChessBoard.tsx      # Chess board display (with flip support)
│   │   ├── NewGameDialog.tsx   # New game modal
│   │   ├── ProtectedRoute.tsx  # Auth guard component
│   │   ├── ChessBoard.module.css
│   │   ├── NewGameDialog.module.css
│   │   └── Layout.tsx
│   ├── context/
│   │   ├── ChessContext.tsx    # Chess game state
│   │   └── AuthContext.tsx     # Authentication state
│   ├── api/
│   │   ├── chessApi.ts         # Chess API client
│   │   ├── authApi.ts          # Auth API client
│   │   ├── statsApi.ts         # Stats API client
│   │   └── matchmakingApi.ts   # Matchmaking API client
│   └── styles/
│       ├── Auth.module.css     # Login/Register styles
│       ├── Layout.module.css   # Layout styles
│       ├── Leaderboard.module.css
│       └── Profile.module.css
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend services running (users-be, game-be, stats-be, matchmaking-be, ai-engine)

### Installation

1. **Install dependencies**:
```bash
cd chess-web-ui
npm install
```

2. **Set up environment** (if needed):
Create `.env.local`:
```
NEXT_PUBLIC_API_BASE=http://localhost:8080
```

3. **Start development server**:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📝 Usage Guide

### 1. Register/Login
- First-time users: Click "Register" to create an account
- Enter username, email, and password
- Login with your credentials
- Session persists across refreshes

### 2. Play Chess
- Click "New Game" button to select:
  - Your color (White/Black)
  - Opponent (currently AI only)
- Click "Flip Board" to rotate the board 180°
- Click "Reset Game" to start fresh

### 3. Check Stats
- Click "Profile" to see your personal statistics:
  - Total games, wins, losses, draws
  - Win rate percentage
- Click "Leaderboard" to see global rankings

## 🔗 API Endpoints Used

### Users Service (Port 8080)
- `POST /api/users` - Register
- `POST /api/users/authenticate` - Login
- `GET /api/users/{uuid}` - Get user
- `GET /api/users/username/{username}` - Get user by username
- `GET /api/users` - List all users

### Stats Service (Port 8080)
- `GET /api/stats/all` - Get leaderboard
- `GET /api/stats/{userId}` - Get player stats
- `POST /api/stats/win/{userId}` - Record win
- `POST /api/stats/loss/{userId}` - Record loss
- `POST /api/stats/draw/{userId}` - Record draw

### Matchmaking Service (Port 8080)
- `POST /api/matches/create` - Create match
- `POST /api/matches/join/{id}` - Join match
- `GET /api/matches` - List matches

### Chess Game (Port 5000 - Flask AI)
- `GET /api/game/get_board` - Get board state
- `POST /api/game/make_move` - Make a move

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Dark Navigation**: Professional dark navbar
- **Color Coding**: 
  - Green (#4CAF50) for success/actions
  - Blue (#2196F3) for secondary actions
  - Orange (#FF9800) for reset
  - Red (#e74c3c) for logout
- **Smooth Animations**: Transitions and hover effects
- **Mobile Menu**: Hamburger menu on small screens

## 🔐 Security Features

- Session-based authentication
- Protected routes redirect to login
- Password validation (min 6 chars)
- User session persists in sessionStorage

## 📚 Technologies Used

- **Next.js 15.3.4** - React framework
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling (available)
- **CSS Modules** - Component-scoped styles
- **Session Storage** - Client-side session management

## ⚙️ Configuration

### API Base URLs (Hardcoded - Update in API files if needed):
- Auth/Stats/Matchmaking: `http://localhost:8080`
- Chess Game: `http://localhost:5000`

To change these, update the `API_BASE` constants in:
- `src/api/authApi.ts`
- `src/api/statsApi.ts`
- `src/api/matchmakingApi.ts`
- `src/api/chessApi.ts`

## 🐛 Troubleshooting

### "Cannot login/register"
- Ensure users-be service is running on port 8080
- Check browser console for CORS errors
- Verify credentials are correct

### "Board not displaying"
- Ensure ai-engine (Flask) is running on port 5000
- Check console for API errors

### "Stats not showing"
- Ensure stats-be is running
- Wait for initial stat creation after first game

## 🚧 Future Enhancements

- [ ] Player vs Player multiplayer (matchmaking integration)
- [ ] Real-time updates with WebSocket
- [ ] ELO rating system
- [ ] Game history replay
- [ ] AI difficulty levels
- [ ] In-game chat
- [ ] Achievement badges
- [ ] Dark mode theme

## 📞 Support

For issues or questions, check:
1. Backend service logs
2. Browser console (F12 → Console)
3. Network tab (F12 → Network) for API calls

---

**Created with ❤️ for Chess Enthusiasts**

