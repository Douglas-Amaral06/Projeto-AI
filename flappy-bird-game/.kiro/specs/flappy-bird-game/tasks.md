# Implementation Tasks: Flappy Bird Game

## Phase 1: Backend Setup

- [x] 1.1 Initialize Node.js Project and Install Dependencies
- [x] 1.2 Create Express Server with Basic Routes
- [x] 1.3 Set Up SQLite Database
- [x] 1.4 Implement Score API Endpoints

## Phase 2: Frontend Structure

- [x] 2.1 Create HTML Structure
- [x] 2.2 Create CSS Styling
- [x] 2.3 Create API Client Module

## Phase 3: Game Entities

- [x] 3.1 Create Entity Base Class
- [x] 3.2 Implement Bird Class
- [x] 3.3 Implement Pipe Class
- [x] 3.4 Implement Ground Class
- [x] 3.5 Implement Collision Detection

## Phase 4: Game Engine and Loop

- [x] 4.1 Create Game Engine Class
- [x] 4.2 Implement Game Loop with requestAnimationFrame
- [x] 4.3 Implement Input Handling
- [x] 4.4 Implement Entity Management
- [x] 4.5 Implement Collision Detection Loop
- [x] 4.6 Implement Rendering System
- [x] 4.7 Implement Game State Management

## Phase 5: Visual Design and UI

- [x] 5.1 Implement Space Background with Planets
- [x] 5.2 Implement Menu Screen
- [x] 5.3 Implement HUD During Gameplay
- [x] 5.4 Implement Game Over Screen
- [x] 5.5 Implement Ranking Display

## Phase 6: Integration and Polish

- [x] 6.1 Connect Frontend to Backend
- [x] 6.2 Implement Score Increment System
- [x] 6.3 Add Visual Polish
- [x] 6.4 Optimize Performance
- [x] 6.5 Test Across Browsers and Devices
- [x] 6.6 Add Comments and Documentation

## Phase 7: Testing and Validation

- [ ] 7.1 Unit Tests for Physics
- [ ] 7.2 Unit Tests for Collision Detection
- [ ] 7.3 Integration Tests
- [ ] 7.4 Property-Based Testing

---

## Detailed Task Descriptions

### Phase 1: Backend Setup

#### 1.1 Initialize Node.js Project and Install Dependencies
- [x] Create `backend/` directory
- [x] Initialize `package.json` with Express, SQLite3, CORS
- [x] Install all dependencies
- [x] Create `.gitignore` for node_modules

**Acceptance Criteria**:
- `npm install` completes without errors
- All dependencies are listed in package.json
- Backend can be started with `npm start`

#### 1.2 Create Express Server with Basic Routes
- [x] Create `backend/server.js`
- [x] Set up Express app on port 3000
- [x] Create GET `/` route to serve static files
- [x] Create GET `/api/scores` route (returns empty array initially)
- [x] Create POST `/api/scores` route (accepts JSON)
- [x] Add CORS middleware
- [x] Add error handling middleware

**Acceptance Criteria**:
- Server starts without errors
- Routes respond with correct status codes
- CORS headers are present
- No console errors

#### 1.3 Set Up SQLite Database
- [x] Create `backend/database.js`
- [x] Initialize SQLite database with scores table
- [x] Table schema: id (PRIMARY KEY), playerName (TEXT), score (INTEGER), timestamp (DATETIME)
- [x] Create functions: createScore(), getTopScores(limit), getAllScores()
- [x] Add input validation and error handling

**Acceptance Criteria**:
- Database file is created
- Table is created with correct schema
- Functions work without errors
- Data persists between server restarts

#### 1.4 Implement Score API Endpoints
- [x] Implement GET /api/scores to return top 10 scores
- [x] Implement POST /api/scores to save new score
- [x] Add validation: playerName (1-20 chars), score (non-negative integer)
- [x] Add error responses with appropriate HTTP status codes
- [x] Test endpoints with curl or Postman

**Acceptance Criteria**:
- GET returns array of scores sorted by score DESC
- POST saves score and returns saved record with id and timestamp
- Invalid input returns 400 Bad Request
- Database errors return 500 Internal Server Error

---

## Phase 2: Frontend Structure

### Task 2.1: Create HTML Structure
- [ ] Create `frontend/index.html`
- [ ] Add canvas element (400x600)
- [ ] Add script tags for game.js, entities.js, api.js
- [ ] Add meta tags for viewport (mobile responsive)
- [ ] Add basic page structure with title

**Acceptance Criteria**:
- HTML is valid and loads without errors
- Canvas is visible in browser
- Scripts load in correct order
- No console errors

### Task 2.2: Create CSS Styling
- [ ] Create `frontend/style.css`
- [ ] Style canvas container (centered, responsive)
- [ ] Style game over modal (semi-transparent overlay)
- [ ] Style input fields and buttons
- [ ] Style ranking display
- [ ] Add responsive design for mobile

**Acceptance Criteria**:
- Canvas is centered on page
- Modal is properly styled
- Buttons are clickable and styled
- Layout works on mobile (320px+)

### Task 2.3: Create API Client Module
- [ ] Create `frontend/api.js`
- [ ] Implement ScoreAPI class with static methods
- [ ] Implement getTopScores(limit = 10)
- [ ] Implement saveScore(playerName, score)
- [ ] Add error handling and retry logic
- [ ] Add loading state management

**Acceptance Criteria**:
- API calls work without errors
- Responses are parsed correctly
- Errors are handled gracefully
- Network failures show user-friendly messages

---

## Phase 3: Game Entities

### Task 3.1: Create Entity Base Class
- [ ] Create `frontend/entities.js`
- [ ] Implement Entity base class with x, y, width, height
- [ ] Add abstract methods: update(deltaTime), render(ctx), getBounds()
- [ ] Add collision detection helper methods

**Acceptance Criteria**:
- Entity class is instantiable
- All methods are defined
- getBounds() returns AABB object

### Task 3.2: Implement Bird Class
- [ ] Extend Entity class
- [ ] Add properties: velocity, gravity (0.6), jumpForce (-12)
- [ ] Implement jump() method
- [ ] Implement update(deltaTime) with gravity physics
- [ ] Implement render(ctx) - draw yellow circle/rectangle
- [ ] Add isAlive property and getter

**Acceptance Criteria**:
- Bird falls with gravity
- Bird jumps on command
- Bird is rendered as yellow shape
- Physics are consistent

### Task 3.3: Implement Pipe Class
- [ ] Extend Entity class
- [ ] Add properties: speed (-4), gapY, gapHeight (120), scored (false)
- [ ] Implement update(deltaTime) - move left
- [ ] Implement render(ctx) - draw two green rectangles (top and bottom)
- [ ] Implement isOffScreen() method
- [ ] Implement hasBeenScored() and markScored() methods

**Acceptance Criteria**:
- Pipes move left at constant speed
- Pipes are rendered correctly
- Off-screen detection works
- Scoring flag works

### Task 3.4: Implement Ground Class
- [ ] Extend Entity class
- [ ] Add properties: speed (-4)
- [ ] Implement update(deltaTime) - move left
- [ ] Implement render(ctx) - draw alternating green/beige rectangles
- [ ] Add looping ground effect (seamless scrolling)

**Acceptance Criteria**:
- Ground moves left
- Ground loops seamlessly
- Ground is rendered with correct colors

### Task 3.5: Implement Collision Detection
- [ ] Create CollisionDetector class in entities.js
- [ ] Implement checkAABB(rect1, rect2) - static method
- [ ] Implement checkBirdPipeCollision(bird, pipe) - static method
- [ ] Implement checkBirdGroundCollision(bird, ground) - static method
- [ ] Implement checkPipeScore(bird, pipe) - static method
- [ ] Add comprehensive comments explaining AABB algorithm

**Acceptance Criteria**:
- AABB collision detection is accurate
- All collision types work correctly
- No false positives or negatives
- Scoring detection is precise

---

## Phase 4: Game Engine and Loop

### Task 4.1: Create Game Engine Class
- [ ] Create `frontend/game.js`
- [ ] Implement GameEngine class with constructor(canvasElement, width, height)
- [ ] Add properties: canvas, ctx, width, height, score, gameState, entities
- [ ] Add state management: 'menu', 'playing', 'gameOver', 'paused'
- [ ] Add getter methods: getScore(), getGameState(), getEntities()

**Acceptance Criteria**:
- GameEngine initializes without errors
- Canvas context is obtained
- State management works
- Getters return correct values

### Task 4.2: Implement Game Loop with requestAnimationFrame
- [ ] Implement start() method
- [ ] Implement update(deltaTime) method
- [ ] Implement render() method
- [ ] Implement gameLoop() with requestAnimationFrame
- [ ] Calculate deltaTime between frames
- [ ] Ensure loop runs at ~60 FPS

**Acceptance Criteria**:
- Game loop runs continuously
- Frame rate is ~60 FPS
- No stuttering or frame drops
- Loop can be stopped

### Task 4.3: Implement Input Handling
- [ ] Implement handleInput(inputType) method
- [ ] Add keyboard listener for Space key
- [ ] Add mouse click listener
- [ ] Add touch listener for mobile
- [ ] Queue inputs for processing in game loop
- [ ] Prevent default behaviors (scroll, etc.)

**Acceptance Criteria**:
- Space key triggers jump
- Mouse click triggers jump
- Touch triggers jump
- No page scrolling on input

### Task 4.4: Implement Entity Management
- [ ] Implement createBird() method
- [ ] Implement createGround() method
- [ ] Implement createPipe() method with random gap
- [ ] Implement spawnPipe() method with timing
- [ ] Implement removePipe(pipe) method
- [ ] Implement updateEntities(deltaTime) method

**Acceptance Criteria**:
- Bird is created at correct position
- Ground is created at correct position
- Pipes are spawned at regular intervals
- Off-screen pipes are removed
- Random gap generation works

### Task 4.5: Implement Collision Detection Loop
- [ ] Implement checkCollisions() method
- [ ] Check bird-pipe collisions for all active pipes
- [ ] Check bird-ground collision
- [ ] Check bird-ceiling collision
- [ ] Update score on pipe crossing
- [ ] Trigger game over on collision

**Acceptance Criteria**:
- Collisions are detected accurately
- Score increments on pipe crossing
- Game over is triggered on collision
- No missed collisions

### Task 4.6: Implement Rendering System
- [ ] Implement render() method
- [ ] Render background (space with stars)
- [ ] Render all pipes
- [ ] Render ground
- [ ] Render bird
- [ ] Render HUD (score)
- [ ] Clear canvas each frame

**Acceptance Criteria**:
- All entities are rendered
- Background is visible
- HUD is visible and readable
- No visual artifacts

### Task 4.7: Implement Game State Management
- [ ] Implement setState(newState) method
- [ ] Implement reset() method
- [ ] Implement gameOver() method
- [ ] Handle transitions between states
- [ ] Pause/resume functionality (optional)

**Acceptance Criteria**:
- State transitions work correctly
- Reset clears all entities and score
- Game over state is set correctly
- State changes are reflected in rendering

---

## Phase 5: Visual Design and UI

### Task 5.1: Implement Space Background with Planets
- [ ] Create background rendering with space theme (dark blue/black)
- [ ] Add stars (small white dots)
- [ ] Implement Planet class for scrolling planets
- [ ] Add 3-5 different planet designs (circles with colors)
- [ ] Planets appear and scroll left as game progresses
- [ ] Planets spawn at different heights and intervals
- [ ] Add parallax effect (planets move slower than pipes)

**Acceptance Criteria**:
- Space background is visible
- Stars are rendered
- Planets appear and scroll
- Planets don't interfere with gameplay
- Visual is appealing

### Task 5.2: Implement Menu Screen
- [ ] Render "Flappy Bird" title (large, centered)
- [ ] Render "Click to Start" text (blinking effect)
- [ ] Render static bird and ground
- [ ] Implement blinking animation (toggle every 500ms)
- [ ] Transition to playing state on input

**Acceptance Criteria**:
- Menu is visually appealing
- Title is prominent
- Text blinks smoothly
- Transition to game is smooth

### Task 5.3: Implement HUD During Gameplay
- [ ] Render score in top-left corner
- [ ] Use large font (24px+)
- [ ] Add white text with black outline for readability
- [ ] Update score every frame
- [ ] Position doesn't obstruct gameplay

**Acceptance Criteria**:
- Score is visible and readable
- Score updates in real-time
- Positioning is good
- No visual artifacts

### Task 5.4: Implement Game Over Screen
- [ ] Create semi-transparent overlay
- [ ] Render "Game Over" text (large, centered)
- [ ] Render final score
- [ ] Create input field for player name
- [ ] Create "Save Score" button
- [ ] Create "Restart" button
- [ ] Add ranking display below buttons

**Acceptance Criteria**:
- Game over screen is visible
- Input field accepts text
- Buttons are clickable
- Ranking is displayed
- Layout is clean and organized

### Task 5.5: Implement Ranking Display
- [ ] Fetch top 10 scores from API
- [ ] Display ranking in table format
- [ ] Show rank, name, score, timestamp
- [ ] Sort by score descending
- [ ] Highlight current player's score
- [ ] Add "Play Again" button

**Acceptance Criteria**:
- Ranking is fetched and displayed
- Scores are sorted correctly
- Current player is highlighted
- Layout is readable

---

## Phase 6: Integration and Polish

### Task 6.1: Connect Frontend to Backend
- [ ] Test API endpoints from frontend
- [ ] Implement score saving flow
- [ ] Implement ranking fetching flow
- [ ] Add loading states
- [ ] Add error messages
- [ ] Test network error handling

**Acceptance Criteria**:
- Scores are saved successfully
- Ranking is fetched and displayed
- Errors are handled gracefully
- No console errors

### Task 6.2: Implement Score Increment System
- [ ] Modify scoring to increment by 1 for each pipe crossed
- [ ] Update HUD to show current score
- [ ] Ensure score persists until game over
- [ ] Test score accuracy

**Acceptance Criteria**:
- Score increments correctly
- Score is accurate
- Score persists during gameplay
- Score resets on new game

### Task 6.3: Add Visual Polish
- [ ] Add smooth animations for transitions
- [ ] Add visual feedback for button clicks
- [ ] Add hover effects on buttons
- [ ] Improve color scheme and contrast
- [ ] Add shadows and depth effects

**Acceptance Criteria**:
- Animations are smooth
- Visual feedback is clear
- Colors are appealing
- No visual glitches

### Task 6.4: Optimize Performance
- [ ] Profile game loop performance
- [ ] Optimize rendering (batch operations)
- [ ] Optimize collision detection
- [ ] Reduce memory allocations
- [ ] Test on low-end devices

**Acceptance Criteria**:
- Game maintains 60 FPS
- Memory usage is stable
- No lag on low-end devices
- Profiler shows good performance

### Task 6.5: Test Across Browsers and Devices
- [ ] Test on Chrome, Firefox, Safari, Edge
- [ ] Test on mobile (iOS, Android)
- [ ] Test on different screen sizes
- [ ] Test touch controls
- [ ] Test keyboard controls

**Acceptance Criteria**:
- Game works on all browsers
- Game works on mobile
- Responsive design works
- All controls work

### Task 6.6: Add Comments and Documentation
- [ ] Add JSDoc comments to all classes and methods
- [ ] Add inline comments for complex logic
- [ ] Document physics equations
- [ ] Document collision detection algorithm
- [ ] Create README with setup instructions

**Acceptance Criteria**:
- Code is well-commented
- Complex logic is explained
- README is clear and complete
- No undocumented functions

---

## Phase 7: Testing and Validation

### Task 7.1: Unit Tests for Physics
- [ ] Test bird gravity application
- [ ] Test bird jump force
- [ ] Test velocity capping
- [ ] Test position updates

**Acceptance Criteria**:
- All physics tests pass
- Physics are accurate
- Edge cases are handled

### Task 7.2: Unit Tests for Collision Detection
- [ ] Test AABB collision detection
- [ ] Test bird-pipe collision
- [ ] Test bird-ground collision
- [ ] Test scoring detection

**Acceptance Criteria**:
- All collision tests pass
- No false positives
- No false negatives

### Task 7.3: Integration Tests
- [ ] Test full game flow (menu → play → game over → ranking)
- [ ] Test score saving and retrieval
- [ ] Test multiple games in sequence
- [ ] Test error scenarios

**Acceptance Criteria**:
- Full game flow works
- Data is persisted correctly
- No data loss
- Errors are handled

### Task 7.4: Property-Based Testing
- [ ] Test score monotonicity (never decreases)
- [ ] Test physics consistency (gravity always applied)
- [ ] Test collision symmetry
- [ ] Test pipe uniqueness (scored once)

**Acceptance Criteria**:
- All properties hold
- No counterexamples found
- Tests are comprehensive

---

## Deliverables

### Backend
- `backend/server.js` - Express server with API routes
- `backend/database.js` - SQLite database setup and queries
- `backend/package.json` - Dependencies

### Frontend
- `frontend/index.html` - HTML structure
- `frontend/style.css` - Styling
- `frontend/game.js` - Game engine and loop
- `frontend/entities.js` - Entity classes and collision detection
- `frontend/api.js` - API client

### Documentation
- `README.md` - Setup and usage instructions
- Code comments and JSDoc

### Testing
- Unit tests for physics and collision
- Integration tests for game flow
- Property-based tests for correctness properties

---

## Success Criteria

- [ ] Game is fully playable in browser
- [ ] All mechanics work correctly (physics, collision, scoring)
- [ ] Backend API works and persists data
- [ ] Frontend and backend communicate correctly
- [ ] Visual design is appealing (space theme with planets)
- [ ] Score increments by 1 for each pipe
- [ ] Game runs at 60 FPS
- [ ] No console errors
- [ ] Works on desktop and mobile
- [ ] Code is well-documented

