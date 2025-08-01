from browser import document, timer, window

# === Constants ===
WIDTH           = 800
LANE_COUNT      = 4

LANE_CENTERS    = [WIDTH / 6, WIDTH / 2, WIDTH * 5 / 6]

size_multi= .5
# ⇢ Bigger cars & player
PLAYER_WIDTH    = 50         # was 50
PLAYER_HEIGHT   = 100       # was 100
PLAYER_COLOR    = "yellow"
BOTTOM_MARGIN   = 10
PLAYER_MOVE_STEP= 20

OBSTACLE_WIDTH = PLAYER_WIDTH
OBSTACLE_HEIGHT = PLAYER_HEIGHT
OBSTACLE_COLORS = ["red", "blue", "green"]

POWERUP_SIZE = 30
POWERUP_COLOR = "cyan"
SHIELD_DURATION = 5000  # ms

DESERT_WIDTH = 80
DECOR_LEFT_X = DESERT_WIDTH / 2
DECOR_RIGHT_X = WIDTH - DESERT_WIDTH / 2
COLLISION_MARGIN = 2

DEC_TYPES = ["cactus", "sign"]

# Difficulty / timing
INITIAL_SPEED = 5
INITIAL_SPAWN_INTERVAL = 1350
MIN_SPAWN_INTERVAL = 400
DECOR_SPAWN_INTERVAL = 800
POWERUP_SPAWN_INTERVAL = 15000
DIFFICULTY_INTERVAL = 8000
SCORE_INTERVAL = 1000
DAY_NIGHT_CYCLE = 60000

# === Global State ===
canvas = document["gameCanvas"]
ctx = canvas.getContext("2d")

HEIGHT = 0                # will be set in update_dimensions()
player_lane = 1            # 0 = left, 1 = centre, 2 = right
player_x = 0               # updated by update_player_pos()
player_y = 0               # updated by reset_player_pos()

obstacles = []
decorations = []
power_ups = []

game_loop_id = None
spawn_timer_id = None
dec_timer_id = None
power_timer_id = None
diff_timer_id = None
score_timer_id = None

keys_down = set()

base_speed = INITIAL_SPEED
spawn_interval = INITIAL_SPAWN_INTERVAL

score = 0
high_score = 0

has_shield = False
shield_expire_time = 0

game_over = False
start_time = 0  # set in restart()

# === High-score persistence ===
try:
    high_score = int(window.localStorage.getItem("desertCabHighScore") or 0)
except Exception:
    high_score = 0

# === Helpers ===============================================================
def recalc_lane_geometry():
    """
    Re-compute everything that depends on the number / width of lanes.
    Call once at start-up *and* from update_dimensions() if the canvas resizes.
    """
    global lane_w, LANE_CENTERS, PLAYER_WIDTH, PLAYER_HEIGHT
    lane_w       = (WIDTH - DESERT_WIDTH * 2) / LANE_COUNT
    LANE_CENTERS = [
        DESERT_WIDTH + lane_w / 2 + i * lane_w
        for i in range(LANE_COUNT)
    ]

    # Cars should almost fill their lane (≈ 85 %)
    PLAYER_WIDTH  = int(lane_w * 0.65)
    PLAYER_HEIGHT = int(PLAYER_WIDTH * 1.69)      # keep the 1 : 2 aspect ratio

    # Obstacles match the player’s footprint
    global OBSTACLE_WIDTH, OBSTACLE_HEIGHT
    OBSTACLE_WIDTH  = PLAYER_WIDTH
    OBSTACLE_HEIGHT = PLAYER_HEIGHT

recalc_lane_geometry()
def update_player_pos():
    """Recompute player_x from player_lane."""
    global player_x
    player_x = LANE_CENTERS[player_lane] - PLAYER_WIDTH / 2

def reset_player_pos():
    """Place the player just above the bottom margin."""
    global player_y
    player_y = HEIGHT - PLAYER_HEIGHT - BOTTOM_MARGIN

def update_dimensions(evt=None):
    global HEIGHT, WIDTH
    # Stretch the HTML element to fill the viewport
    canvas.style.width  = f"{window.innerWidth}px"
    canvas.style.height = f"{window.innerHeight}px"
    # Match the drawing buffer to that new size
    canvas.width  = window.innerWidth
    canvas.height = window.innerHeight

    HEIGHT = canvas.height
    WIDTH  = canvas.width

    reset_player_pos()
    recalc_lane_geometry()
    draw_everything()
def boxes_intersect(x1, y1, w1, h1, x2, y2, w2, h2, margin=0):
    return (
        x1 + margin < x2 + w2 - margin
        and x1 + w1 - margin > x2 + margin
        and y1 + margin < y2 + h2 - margin
        and y1 + h1 - margin > y2 + margin
    )

# ---------------- spawn helpers (unchanged except for HEIGHT removal) ------

# near the top of your file, keep these
last_spawn_lane        = None
second_last_spawn_lane = None
double_cooldown = 0

def spawn_obstacle():
    global last_spawn_lane, second_last_spawn_lane, double_cooldown

    # decide if we’re allowed to do a double
    can_double = (double_cooldown <= 0)
    if can_double and window.Math.random() < 0.2:
        num_to_spawn = 2
    else:
        num_to_spawn = 1

    def lanes_clear_of_adjacent():
        safe = []
        for lane in range(LANE_COUNT):
            ok = True
            for adj in (lane - 1, lane + 1):
                if 0 <= adj < LANE_COUNT:
                    for o in obstacles:
                        if o["lane"] == adj and o["y"] < OBSTACLE_HEIGHT:
                            ok = False
                            break
                    if not ok:
                        break
            if ok:
                safe.append(lane)
        return safe

    lanes_to_spawn = []
    if num_to_spawn == 1:
        safe = lanes_clear_of_adjacent()
        if safe:
            # penalize 3-in-a-row lane
            penalized = (
                last_spawn_lane is not None
                and last_spawn_lane == second_last_spawn_lane
            )
            weights = []
            for lane in safe:
                weights.append(2 if (penalized and lane == last_spawn_lane) else 3)

            total = sum(weights)
            pick = window.Math.random() * total
            running = 0
            for lane, w in zip(safe, weights):
                running += w
                if pick < running:
                    chosen = lane
                    break
            lanes_to_spawn = [chosen]
        else:
            lanes_to_spawn = [ _choose_best_lane_by_same_lane_clearance() ]

        # update history
        second_last_spawn_lane = last_spawn_lane
        last_spawn_lane        = lanes_to_spawn[0]

    else:
        # double‐spawn: pick a random adjacent pair
        pairs = [(i, i+1) for i in range(LANE_COUNT - 1)]
        lane1, lane2 = pairs[int(window.Math.floor(window.Math.random() * len(pairs)))]
        lanes_to_spawn = [lane1, lane2]

        # reset single‐spawn history
        last_spawn_lane = None
        second_last_spawn_lane = None

    # actually add the obstacles
    for lane in lanes_to_spawn:
        obstacles.append({
            "lane":   lane,
            "x":      LANE_CENTERS[lane] - OBSTACLE_WIDTH / 2,
            "y":     -OBSTACLE_HEIGHT,
            "width":  OBSTACLE_WIDTH,
            "height": OBSTACLE_HEIGHT,
            "speed":  base_speed + window.Math.random(),
            "color":  OBSTACLE_COLORS[
                int(window.Math.floor(
                    window.Math.random() * len(OBSTACLE_COLORS)
                ))
            ]
        })

    # update our double‐spawn cooldown
    if num_to_spawn == 2:
        double_cooldown = 3
    elif double_cooldown > 0:
        double_cooldown -= 1

def _choose_best_lane_by_same_lane_clearance():
    """Your existing fallback: pick the lane where the nearest car in that same lane
       is furthest down the screen, so you don’t bunch on top of yourself."""
    best_lane, max_dist = None, -1
    for l in range(LANE_COUNT):
        nearest = min(
            (o["y"] for o in obstacles if o["lane"] == l),
            default=HEIGHT + 100
        )
        if nearest > max_dist:
            best_lane, max_dist = l, nearest
    return best_lane


def spawn_decoration():
    dtype = DEC_TYPES[int(window.Math.floor(window.Math.random() * len(DEC_TYPES)))]
    side  = "left" if window.Math.random() < 0.5 else "right"
    x     = DECOR_LEFT_X if side == "left" else DECOR_RIGHT_X
    if dtype == "cactus":
        width, height, color = 20, int(40 + window.Math.floor(window.Math.random() * 41)), "green"
    else:
        width, height, color = 10, 40, "brown"
    decorations.append({"type": dtype, "x": x, "y": -height,
                        "width": width, "height": height, "color": color})

def spawn_power_up():
    lane = int(window.Math.floor(window.Math.random() * LANE_COUNT))
    power_ups.append({"lane": lane,
                      "x": LANE_CENTERS[lane] - POWERUP_SIZE / 2,
                      "y": -POWERUP_SIZE,
                      "size": POWERUP_SIZE,
                      "color": POWERUP_COLOR})

# ---------------- collision & game logic -----------------------------------

def check_collisions():
    global game_over, has_shield, high_score
    if game_over:
        return
    for obs in list(obstacles):
        if boxes_intersect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT,
                           obs["x"], obs["y"], obs["width"], obs["height"], COLLISION_MARGIN):
            if has_shield:
                obstacles.remove(obs)
                has_shield = False
            else:
                game_over = True
                if score > high_score:
                    high_score = score
                    window.localStorage.setItem("desertCabHighScore", str(high_score))
            return

def check_powerup_collision():
    global has_shield, shield_expire_time
    if game_over:
        return
    now = window.Date.now()
    for pu in list(power_ups):
        if boxes_intersect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT,
                           pu["x"], pu["y"], pu["size"], pu["size"], 0):
            has_shield, shield_expire_time = True, now + SHIELD_DURATION
            power_ups.remove(pu)
            return

def difficulty_ramp():
    global base_speed, spawn_interval, spawn_timer_id
    base_speed += 1                     # same increment, happens twice as often
    new_interval = max(spawn_interval - 150, MIN_SPAWN_INTERVAL)  # drops quicker
    if new_interval != spawn_interval:
        spawn_interval = new_interval
        timer.clear_interval(spawn_timer_id)
        spawn_timer_id = timer.set_interval(spawn_obstacle, spawn_interval)
def increment_score():
    global score
    if not game_over:
        score += 1

# ---------------- drawing ---------------------------------------------------

def draw_everything():
    # Background & road
    ctx.fillStyle = "yellow"
    ctx.fillRect(0, 0, WIDTH, HEIGHT)
    ctx.fillStyle = "#555"
    ctx.fillRect(DESERT_WIDTH, 0, WIDTH - DESERT_WIDTH * 2, HEIGHT)

    # Lane dashed lines
    ctx.strokeStyle = "white"
    ctx.setLineDash([20, 15])
    ctx.lineWidth = 4
    for i in range(1, LANE_COUNT):
        x = DESERT_WIDTH + lane_w * i  # use the real road, not the full canvas
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, HEIGHT)
        ctx.stroke()
    ctx.setLineDash([])
    ctx.lineWidth = 1

    # Decorations
    for d in decorations:
        ctx.fillStyle = d["color"]
        ctx.fillRect(d["x"], d["y"], d["width"], d["height"])
        if d["type"] == "sign":
            ctx.fillStyle = "white"
            ctx.fillRect(d["x"] - 10, d["y"] - 20, 30, 20)

    # Power-ups
    for p in power_ups:
        ctx.fillStyle = p["color"]
        ctx.fillRect(p["x"], p["y"], p["size"], p["size"])

    # Obstacles
    for o in obstacles:
        ctx.fillStyle = o["color"]
        ctx.fillRect(o["x"], o["y"], o["width"], o["height"])
        ctx.fillStyle = "black"
        ctx.beginPath(); ctx.arc(o["x"] + 10,               o["y"] + 5, 5, 0, 2 * window.Math.PI); ctx.fill()
        ctx.beginPath(); ctx.arc(o["x"] + o["width"] - 10,  o["y"] + 5, 5, 0, 2 * window.Math.PI); ctx.fill()

    # Player
    ctx.fillStyle = PLAYER_COLOR
    ctx.fillRect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    ctx.fillStyle = "black"
    ctx.beginPath(); ctx.arc(player_x + 10,             player_y + 5, 5, 0, 2 * window.Math.PI); ctx.fill()
    ctx.beginPath(); ctx.arc(player_x + PLAYER_WIDTH-10, player_y + 5, 5, 0, 2 * window.Math.PI); ctx.fill()
    if has_shield:
        ctx.strokeStyle = "cyan"; ctx.lineWidth = 5
        ctx.strokeRect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        ctx.lineWidth = 1

    # Score UI
    ctx.font = "20px sans-serif"

    def draw_outlined(txt, x, y):
        ctx.lineWidth = 3
        ctx.strokeStyle = "black"
        ctx.strokeText(txt, x, y)
        ctx.fillStyle = "white"
        ctx.fillText(txt, x, y)

    draw_outlined(f"Score: {score}", 10, 30)
    draw_outlined(f"High Score: {high_score}", 10, 60)

    # Game-over banner
    if game_over:
        # make the backdrop a bit taller
        ctx.fillStyle = "rgba(0,0,0,0.6)"
        ctx.fillRect(0, HEIGHT / 2 - 40, WIDTH, 120)

        # big GAME OVERa
        ctx.fillStyle = "red"
        ctx.font = "40px sans-serif"
        ctx.fillText("🚨 GAME OVER 🚨", WIDTH / 2 - 160, HEIGHT / 2 + 10)

        # your score, smaller
        ctx.font = "24px sans-serif"
        ctx.fillStyle = "white"
        ctx.fillText(f"Your score: {score}", WIDTH / 2 - 80, HEIGHT / 2 + 45)

        # restart hint
        ctx.font = "20px sans-serif"
        ctx.fillText("Click to Restart", WIDTH/2 - 90, HEIGHT/2 + 75)
    # Day/night overlay
    elapsed = window.Date.now() - start_time
    # if (elapsed % DAY_NIGHT_CYCLE) >= DAY_NIGHT_CYCLE / 2:
    #     ctx.fillStyle = "rgba(0,0,0,0.5)"
    #     ctx.fillRect(0, 0, WIDTH, HEIGHT)

# ---------------- main loop -------------------------------------------------

def update(dt=None):
    global has_shield
    if game_over:
        draw_everything()
        return

    # Move entities
    for obs in obstacles:  obs["y"] += obs["speed"]
    obstacles[:] = [o for o in obstacles if o["y"] < HEIGHT + 50]

    for dec in decorations: dec["y"] += base_speed
    decorations[:] = [d for d in decorations if d["y"] < HEIGHT + 50]

    for p in power_ups: p["y"] += base_speed
    power_ups[:] = [p for p in power_ups if p["y"] < HEIGHT + 50]

    # Player movement (keys)
    move_x = ("ArrowRight" in keys_down) - ("ArrowLeft" in keys_down)
    move_y = ("ArrowDown"  in keys_down) - ("ArrowUp"   in keys_down)
    if move_x or move_y:
        global player_x, player_y
        player_x += move_x * PLAYER_MOVE_STEP
        player_y += move_y * PLAYER_MOVE_STEP
        # Bounds
        player_x = max(DESERT_WIDTH, min(player_x, WIDTH - DESERT_WIDTH - PLAYER_WIDTH))
        player_y = max(0, min(player_y, HEIGHT - PLAYER_HEIGHT - BOTTOM_MARGIN))

    # Collisions & shield timer
    check_collisions()
    check_powerup_collision()
    if has_shield and window.Date.now() >= shield_expire_time:
        has_shield = False

    draw_everything()

# ---------------- restart / setup ------------------------------------------

def restart():
    global obstacles, decorations, power_ups, score, game_over
    global base_speed, spawn_interval, has_shield, shield_expire_time, start_time
    global spawn_timer_id, dec_timer_id, power_timer_id, diff_timer_id, score_timer_id, game_loop_id

    # Clear timers
    for tid in [spawn_timer_id, dec_timer_id, power_timer_id, diff_timer_id, score_timer_id, game_loop_id]:
        if tid is not None:
            try: timer.clear_interval(tid)
            except Exception: pass
    recalc_lane_geometry()
    # Reset game state
    obstacles, decorations, power_ups = [], [], []
    score, game_over = 0, False
    base_speed, spawn_interval = INITIAL_SPEED, INITIAL_SPAWN_INTERVAL
    has_shield, shield_expire_time = False, 0

    update_dimensions()  # resizes canvas & also calls reset_player_pos()
    update_player_pos()
    start_time = window.Date.now()

    # Timers
    game_loop_id   = timer.set_interval(update, 16)
    spawn_timer_id = timer.set_interval(spawn_obstacle, spawn_interval)
    dec_timer_id   = timer.set_interval(spawn_decoration, DECOR_SPAWN_INTERVAL)
    power_timer_id = timer.set_interval(spawn_power_up, POWERUP_SPAWN_INTERVAL)
    diff_timer_id  = timer.set_interval(difficulty_ramp, DIFFICULTY_INTERVAL)
    score_timer_id = timer.set_interval(increment_score, SCORE_INTERVAL)

    draw_everything()

# ---------------- input -----------------------------------------------------
def on_touch(evt):
    evt.preventDefault()
    global player_lane, game_over
    # if we’re on the game-over screen, restart immediately
    if game_over:
        restart()
        return

    # otherwise treat it as a lane-change tap
    t = evt.touches[0]
    x = t.clientX
    mid = window.innerWidth / 2
    if x < mid:
        player_lane = max(0, player_lane - 1)
    else:
        player_lane = min(LANE_COUNT - 1, player_lane + 1)

    update_player_pos()
    draw_everything()

document["gameCanvas"].bind("touchstart", on_touch)
def on_keydown(evt):
    key = evt.key
    keys_down.add(key)
    if (key == "r" or key == "R") and game_over:
        restart()
def on_click(evt):
    # if we’re in game-over state, any click/tap restarts
    if game_over:
        restart()


def on_keyup(evt):
    keys_down.discard(evt.key)

document.bind("keydown", on_keydown)
document.bind("keyup", on_keyup)
document.bind("click", on_click)


# ---------------- initialisation -------------------------------------------

update_dimensions()               # sets HEIGHT, player_y, canvas.height
update_player_pos()
window.bind("resize", update_dimensions)

# Expose a JS-callable start
window.start_game = restart

draw_everything()                 # first frame while waiting for user
