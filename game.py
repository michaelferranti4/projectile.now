from browser import document, timer, window

# === Constants ===
WIDTH = window.innerWidth
HEIGHT = window.innerHeight  # use full screen height

LANE_COUNT = 3
DESERT_WIDTH = 80  # width of desert strip on each side
ROAD_WIDTH = WIDTH - DESERT_WIDTH * 2
LANE_WIDTH = ROAD_WIDTH / LANE_COUNT
LANE_CENTERS = [DESERT_WIDTH + LANE_WIDTH / 2 + i * LANE_WIDTH for i in range(LANE_COUNT)]

PLAYER_WIDTH = 60
PLAYER_HEIGHT = 110
PLAYER_COLOR = "yellow"
PLAYER_START_LANE = 1  # 0=left, 1=center, 2=right
PLAYER_START_Y = HEIGHT - PLAYER_HEIGHT - 10  # 10px from bottom
PLAYER_MOVE_STEP = 20

OBSTACLE_WIDTH = PLAYER_WIDTH
OBSTACLE_HEIGHT = PLAYER_HEIGHT
OBSTACLE_COLORS = ["red", "blue", "green"]

POWERUP_SIZE = 30
POWERUP_COLOR = "cyan"
SHIELD_DURATION = 5000  # ms of invulnerability

DECOR_LEFT_X = DESERT_WIDTH / 2
DECOR_RIGHT_X = WIDTH - DESERT_WIDTH / 2
COLLISION_MARGIN = 10

DEC_TYPES = ["cactus", "sign"]

# Difficulty / timing
INITIAL_SPEED = 3  # px per frame (slightly faster)
INITIAL_SPAWN_INTERVAL = 2000  # ms between obstacles
MIN_SPAWN_INTERVAL = 700
DECOR_SPAWN_INTERVAL = 1000  # ms
POWERUP_SPAWN_INTERVAL = 15000  # ms
DIFFICULTY_INTERVAL = 30000  # every 30 seconds
SCORE_INTERVAL = 1000  # every second

DAY_NIGHT_CYCLE = 60000  # full cycle in ms (30s day, 30s night)


# === Global State ===
canvas = document["gameCanvas"]
canvas.width = WIDTH
canvas.height = HEIGHT  # ensure canvas matches full screen height
ctx = canvas.getContext("2d")

player_lane = PLAYER_START_LANE
player_x = LANE_CENTERS[player_lane] - PLAYER_WIDTH / 2
player_y = PLAYER_START_Y

# Lists of active game objects
obstacles = []
decorations = []
power_ups = []

# Timers (store IDs so we can clear/replace)
game_loop_id = None
spawn_timer_id = None
dec_timer_id = None
power_timer_id = None
diff_timer_id = None
score_timer_id = None

# Currently pressed keys for smooth movement
keys_down = set()

# Game variables
base_speed = INITIAL_SPEED
spawn_interval = INITIAL_SPAWN_INTERVAL

score = 0
high_score = 0

has_shield = False
shield_expire_time = 0

game_over = False
start_time = 0  # timestamp at game start: used for day/night

# === Helpers to retrieve/store high score ===
item = window.localStorage.getItem("desertCabHighScore")
if item:
    try:
        high_score = int(item)
    except:
        high_score = 0
else:
    high_score = 0


# === Utility Functions ===
def update_player_pos():
    """Recompute player_x from player_lane."""
    global player_x
    player_x = LANE_CENTERS[player_lane] - PLAYER_WIDTH / 2


def boxes_intersect(x1, y1, w1, h1, x2, y2, w2, h2, margin=0):
    """Return True if the two rectangles intersect with optional margin."""
    return (
        x1 + margin < x2 + w2 - margin
        and x1 + w1 - margin > x2 + margin
        and y1 + margin < y2 + h2 - margin
        and y1 + h1 - margin > y2 + margin
    )


def spawn_obstacle():
    """Create a new obstacle in a random lane, moving downward."""
    # avoid stacking obstacles too closely at the top
    attempts = 0
    lane = int(window.Math.floor(window.Math.random() * LANE_COUNT))
    while attempts < 5:
        if not any(
            o["lane"] == lane and o["y"] < OBSTACLE_HEIGHT * 2 for o in obstacles
        ):
            break
        lane = int(window.Math.floor(window.Math.random() * LANE_COUNT))
        attempts += 1
    x = LANE_CENTERS[lane] - OBSTACLE_WIDTH / 2
    y = -OBSTACLE_HEIGHT
    speed = base_speed + window.Math.random() * 1  # small variation
    color = OBSTACLE_COLORS[int(window.Math.floor(window.Math.random() * len(OBSTACLE_COLORS)))]
    obstacles.append(
        {
            "lane": lane,
            "x": x,
            "y": y,
            "width": OBSTACLE_WIDTH,
            "height": OBSTACLE_HEIGHT,
            "speed": speed,
            "color": color,
        }
    )


def spawn_decoration():
    """Spawn a decorative cactus or sign on either side, scrolling downward."""
    dtype = DEC_TYPES[int(window.Math.floor(window.Math.random() * len(DEC_TYPES)))]
    side = "left" if window.Math.random() < 0.5 else "right"
    if side == "left":
        x = DECOR_LEFT_X
    else:
        x = DECOR_RIGHT_X

    if dtype == "cactus":
        width = 20
        height = int(40 + window.Math.floor(window.Math.random() * 41))  # 40–80 px tall
        color = "green"
    else:  # sign
        width = 10
        height = 40
        color = "brown"

    y = -height
    decorations.append(
        {
            "type": dtype,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": color,
        }
    )


def spawn_power_up():
    """Spawn a shield power‐up in a random lane."""
    lane = int(window.Math.floor(window.Math.random() * LANE_COUNT))
    x = LANE_CENTERS[lane] - POWERUP_SIZE / 2
    y = -POWERUP_SIZE
    power_ups.append(
        {
            "lane": lane,
            "x": x,
            "y": y,
            "size": POWERUP_SIZE,
            "color": POWERUP_COLOR,
        }
    )


def check_collisions():
    """Detect collisions between player and obstacles."""
    global game_over, has_shield, high_score

    # Only check if game is still running
    if game_over:
        return

    for obs in list(obstacles):
        if boxes_intersect(
            player_x,
            player_y,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
            obs["x"],
            obs["y"],
            obs["width"],
            obs["height"],
            COLLISION_MARGIN,
        ):
            if has_shield:
                try:
                    obstacles.remove(obs)
                except ValueError:
                    pass
                has_shield = False
                return
            else:
                game_over = True
                if score > high_score:
                    high_score = score
                    window.localStorage.setItem(
                        "desertCabHighScore", str(high_score)
                    )
                return


def check_powerup_collision():
    """Detect if player picks up a power‐up."""
    global has_shield, shield_expire_time

    if game_over:
        return

    now = window.Date.now()

    for pu in list(power_ups):
        if boxes_intersect(
            player_x,
            player_y,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
            pu["x"],
            pu["y"],
            pu["size"],
            pu["size"],
            0,
        ):
            has_shield = True
            shield_expire_time = now + SHIELD_DURATION
            try:
                power_ups.remove(pu)
            except ValueError:
                pass
            return


def difficulty_ramp():
    """Called every DIFFICULTY_INTERVAL ms: speeds up and tightens spawn interval."""
    global base_speed, spawn_interval, spawn_timer_id

    base_speed += 1  # increase downward scroll
    new_interval = max(spawn_interval - 100, MIN_SPAWN_INTERVAL)
    if new_interval != spawn_interval:
        spawn_interval = new_interval
        # reset obstacle‐spawn timer to new interval
        if spawn_timer_id is not None:
            timer.clear_interval(spawn_timer_id)
        spawn_timer_id = timer.set_interval(spawn_obstacle, spawn_interval)


def increment_score():
    """Add 1 point every second, if the game is running."""
    global score
    if not game_over:
        score += 1


def draw_everything():
    """Draw background, road, lanes, decorations, obstacles, player, power‐ups, UI, and day/night overlay."""
    # Clear background with desert color then draw the road
    ctx.fillStyle = "yellow"
    ctx.fillRect(0, 0, WIDTH, HEIGHT)
    ctx.fillStyle = "#222"  # road color
    ctx.fillRect(DESERT_WIDTH, 0, WIDTH - DESERT_WIDTH * 2, HEIGHT)

    # Draw lane separators (dashed white lines)
    ctx.strokeStyle = "white"
    ctx.setLineDash([20, 15])
    ctx.lineWidth = 4
    for i in range(1, LANE_COUNT):
        x = DESERT_WIDTH + LANE_WIDTH * i
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, HEIGHT)
        ctx.stroke()
    ctx.setLineDash([])
    ctx.lineWidth = 1

    # Draw decorations behind obstacles
    for dec in decorations:
        if dec["type"] == "cactus":
            ctx.fillStyle = dec["color"]
            ctx.fillRect(dec["x"], dec["y"], dec["width"], dec["height"])
        else:  # sign
            # Draw post
            ctx.fillStyle = dec["color"]
            ctx.fillRect(dec["x"], dec["y"], dec["width"], dec["height"])
            # Draw sign board above post
            ctx.fillStyle = "white"
            ctx.fillRect(dec["x"] - 10, dec["y"] - 20, 30, 20)

    # Draw power‐ups
    for pu in power_ups:
        ctx.fillStyle = pu["color"]
        ctx.fillRect(pu["x"], pu["y"], pu["size"], pu["size"])

    # Draw obstacles
    for obs in obstacles:
        ctx.fillStyle = obs["color"]
        ctx.fillRect(obs["x"], obs["y"], obs["width"], obs["height"])
        # wheels
        ctx.fillStyle = "black"
        ctx.beginPath()
        ctx.arc(obs["x"] + 10, obs["y"] + obs["height"] - 5, 5, 0, 2 * window.Math.PI)
        ctx.fill()
        ctx.beginPath()
        ctx.arc(obs["x"] + obs["width"] - 10, obs["y"] + obs["height"] - 5, 5, 0, 2 * window.Math.PI)
        ctx.fill()

    # Draw player
    ctx.fillStyle = PLAYER_COLOR
    ctx.fillRect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    # player wheels
    ctx.fillStyle = "black"
    ctx.beginPath()
    ctx.arc(player_x + 10, player_y + PLAYER_HEIGHT - 5, 5, 0, 2 * window.Math.PI)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(player_x + PLAYER_WIDTH - 10, player_y + PLAYER_HEIGHT - 5, 5, 0, 2 * window.Math.PI)
    ctx.fill()
    if has_shield:
        ctx.strokeStyle = "cyan"
        ctx.lineWidth = 5
        ctx.strokeRect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        ctx.lineWidth = 1

    # Draw score & high score
    ctx.font = "20px sans-serif"
    ctx.lineWidth = 3
    ctx.strokeStyle = "black"
    ctx.fillStyle = "white"
    ctx.strokeText(f"Score: {score}", 10, 30)
    ctx.fillText(f"Score: {score}", 10, 30)
    ctx.strokeText(f"High Score: {high_score}", 10, 60)
    ctx.fillText(f"High Score: {high_score}", 10, 60)

    # If game over, overlay a semi‐transparent rectangle and text
    if game_over:
        ctx.fillStyle = "rgba(0, 0, 0, 0.6)"
        ctx.fillRect(0, HEIGHT / 2 - 40, WIDTH, 80)
        ctx.fillStyle = "red"
        ctx.font = "40px sans-serif"
        ctx.fillText("🚨 GAME OVER 🚨", WIDTH / 2 - 160, HEIGHT / 2 + 10)
        ctx.font = "20px sans-serif"
        ctx.fillStyle = "white"
        ctx.fillText("Press R to Restart", WIDTH / 2 - 90, HEIGHT / 2 + 40)

    # Day‐Night overlay (darken screen if in “night” half of cycle)
    now = window.Date.now()
    elapsed = now - start_time
    cycle_pos = (elapsed % DAY_NIGHT_CYCLE) / DAY_NIGHT_CYCLE
    # cycle_pos ∈ [0,1). If ≥0.5 → night
    if cycle_pos >= 0.5:
        ctx.fillStyle = "rgba(0, 0, 0, 0.5)"
        ctx.fillRect(0, 0, WIDTH, HEIGHT)


def update(dt=None):
    """Main game‐loop: move everything, check collisions, and redraw."""
    global game_over, has_shield

    if game_over:
        # Even if game is over, we still draw once more to show the Game Over overlay
        draw_everything()
        return

    # Move obstacles down
    for obs in obstacles:
        obs["y"] += obs["speed"]
    # Remove obstacles that left the screen
    obstacles[:] = [o for o in obstacles if o["y"] < HEIGHT + 50]

    # Move decorations
    for dec in decorations:
        dec["y"] += base_speed
    decorations[:] = [d for d in decorations if d["y"] < HEIGHT + 50]

    # Move power‐ups
    for pu in power_ups:
        pu["y"] += base_speed
    power_ups[:] = [p for p in power_ups if p["y"] < HEIGHT + 50]

    # Smooth player movement based on keys held
    move_x = 0
    move_y = 0
    if "ArrowLeft" in keys_down:
        move_x -= PLAYER_MOVE_STEP
    if "ArrowRight" in keys_down:
        move_x += PLAYER_MOVE_STEP
    if "ArrowUp" in keys_down:
        move_y -= PLAYER_MOVE_STEP
    if "ArrowDown" in keys_down:
        move_y += PLAYER_MOVE_STEP
    if move_x or move_y:
        global player_x, player_y
        player_x += move_x
        player_y += move_y
        if player_x < DESERT_WIDTH:
            player_x = DESERT_WIDTH
        if player_x > WIDTH - DESERT_WIDTH - PLAYER_WIDTH:
            player_x = WIDTH - DESERT_WIDTH - PLAYER_WIDTH
        if player_y < 0:
            player_y = 0
        if player_y > HEIGHT - PLAYER_HEIGHT - 10:
            player_y = HEIGHT - PLAYER_HEIGHT - 10

    # Collision checks
    check_collisions()
    check_powerup_collision()

    # Shield expiration
    if has_shield and window.Date.now() >= shield_expire_time:
        has_shield = False

    # Redraw everything
    draw_everything()


def restart():
    """Reset all game state and restart all timers."""
    global obstacles, decorations, power_ups
    global score, game_over, base_speed, spawn_interval
    global player_lane, player_y, start_time, has_shield, shield_expire_time
    global spawn_timer_id, dec_timer_id, power_timer_id, diff_timer_id, score_timer_id, game_loop_id

    # Clear previous timers
    for tid in [spawn_timer_id, dec_timer_id, power_timer_id, diff_timer_id, score_timer_id, game_loop_id]:
        if tid is not None:
            try:
                timer.clear_interval(tid)
            except:
                pass

    # Reset variables
    obstacles = []
    decorations = []
    power_ups = []
    score = 0
    game_over = False
    base_speed = INITIAL_SPEED
    spawn_interval = INITIAL_SPAWN_INTERVAL

    player_lane = PLAYER_START_LANE
    player_y = PLAYER_START_Y
    update_player_pos()
    has_shield = False
    shield_expire_time = 0

    start_time = window.Date.now()

    # Re‐start timers
    game_loop_id = timer.set_interval(update, 16)  # ~60 FPS
    spawn_timer_id = timer.set_interval(spawn_obstacle, spawn_interval)
    dec_timer_id = timer.set_interval(spawn_decoration, DECOR_SPAWN_INTERVAL)
    power_timer_id = timer.set_interval(spawn_power_up, POWERUP_SPAWN_INTERVAL)
    diff_timer_id = timer.set_interval(difficulty_ramp, DIFFICULTY_INTERVAL)
    score_timer_id = timer.set_interval(increment_score, SCORE_INTERVAL)

# Immediately draw the first frame
    draw_everything()

# === Input Handling ===
def on_keydown(evt):
    """Track keys being pressed for smooth movement."""
    key = evt.key
    keys_down.add(key)
    if (key == "r" or key == "R") and game_over:
        restart()


def on_keyup(evt):
    """Remove keys from the pressed set when released."""
    key = evt.key
    if key in keys_down:
        keys_down.remove(key)


document.bind("keydown", on_keydown)
document.bind("keyup", on_keyup)


# Expose game start to JavaScript. The game will begin when
# window.start_game() is called from JS after user interaction.
window.start_game = restart
