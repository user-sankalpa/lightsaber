# =========================
# GLOBAL HELPER FUNCTION
# =========================

def draw_arrow(direction, size):
    """
    Draw an arrow (chevron shape) using two lines.
    This function is called by the Target class.
    We are drawing relative to (0,0), which will be the center of the target.
    """
    # 's' determines the size of the chevron based on the target's overall size
    s = size * 0.3  
    
    # We are drawing at (0,0) which is the center of the target
    if direction == "up":
        # line(x1, y1, x2, y2)
        # Draws a '^' shape
        line(-s, s, 0, -s)  # Left line: from bottom-left (-s, s) to top-center (0, -s)
        line(0, -s, s, s)   # Right line: from top-center (0, -s) to bottom-right (s, s)
    elif direction == "down":
        # Draws a 'v' shape
        line(-s, -s, 0, s)
        line(0, s, s, -s)
    elif direction == "left":
        # Draws a '<' shape
        line(s, -s, -s, 0)
        line(-s, 0, s, s)
    elif direction == "right":
        # Draws a '>' shape
        line(-s, -s, s, 0)
        line(s, 0, -s, s)

# =========================
# LANE CLASS
# =========================
# A Lane defines one of the four "tracks" the targets travel on.
# Its main job is to calculate the 2D position and scale of a target
# based on its "progress" (0.0 to 1.0), creating the 3D illusion.
#
class Lane:
    def __init__(self, lane_id, direction, vp_x, vp_y, end_x, end_y):
        self.lane_id = lane_id
        self.direction = direction  # "left", "right", "up", "down"
        
        # Vanishing Point (where the lane starts, in the distance)
        self.vp_x = vp_x
        self.vp_y = vp_y
        
        # End Point (where the lane ends, at the hit line)
        self.end_x = end_x
        self.end_y = end_y
        
        # The lane itself is a trapezoid, narrow at the start and wide at the end
        self.lane_width_start = 2
        self.lane_width_end = 60
    
    def get_position(self, progress):
        """
        Calculates the (x, y) coordinate along the lane for a given progress.
        'progress' is a number from 0.0 (at the vanishing point) to 1.0 (at the end point).
        
        This is a "Linear Interpolation" (or 'lerp') formula:
        result = start + (end - start) * progress
        """
        x = self.vp_x + (self.end_x - self.vp_x) * progress
        y = self.vp_y + (self.end_y - self.vp_y) * progress
        return x, y
    
    def get_scale(self, progress):
        """
        Calculates the scale multiplier for a given progress.
        Targets are small (0.1) at the vanishing point and large (1.0) at the end.
        This uses the same Linear Interpolation formula.
        """
        min_scale = 0.1
        max_scale = 1.0
        return min_scale + (max_scale - min_scale) * progress
    
    def get_width(self, progress):
        """
        Calculates the visual width of the lane itself at a given progress.
        """
        return self.lane_width_start + (self.lane_width_end - self.lane_width_start) * progress
    
    def draw(self):
        """Draws the lane as a 3D trapezoid"""
        stroke(100, 100, 150, 100)
        strokeWeight(2)
        
        # Calculate the left/right offsets from the center for both ends
        start_offset_left = -self.lane_width_start / 2
        start_offset_right = self.lane_width_start / 2
        end_offset_left = -self.lane_width_end / 2
        end_offset_right = self.lane_width_end / 2
        
        # Draw the left edge of the trapezoid
        line(self.vp_x + start_offset_left, self.vp_y,
             self.end_x + end_offset_left, self.end_y)
        # Draw the right edge of the trapezoid
        line(self.vp_x + start_offset_right, self.vp_y,
             self.end_x + end_offset_right, self.end_y)
        
        # Draw the center line
        stroke(150, 150, 200, 150)
        strokeWeight(1)
        line(self.vp_x, self.vp_y, self.end_x, self.end_y)
        
        # Draw the direction indicator (L, D, U, R) at the end of the lane
        pushMatrix()
        translate(self.end_x, self.end_y)
        fill(200, 200, 255, 100)
        noStroke()
        textSize(12)
        textAlign(CENTER, CENTER)
        text(self.direction.upper()[0], 0, 0)
        popMatrix()

# =========================
# TARGET CLASS
# =========================
# A Target is the "note" that travels down a specific lane.
# It manages its own position (progress), type (red/blue), and state (active/hit).
#
class Target:
    def __init__(self, lane, target_type, speed):
        self.lane = lane  # The Lane object this target belongs to
        self.target_type = target_type  # "red", "blue", or "bomb"
        self.direction = lane.direction # The direction this target requires
        
        self.progress = 0.0
        self.speed = speed # Set by the GameManager
        self.base_size = 80
        
        # State variables
        self.active = True
        self.in_hit_zone = False
        self.was_hit = False # "Memory" to prevent the "miss" bug
        
        # --- HIT ZONE LOGIC ---
        self.hit_zone_start = 0.75 # Progress must be *at least* 0.75
        self.hit_zone_end = 1.0   # Progress must be *at most* 1.0
    
    def update(self):
        """Updates the target's position and state each frame"""
        if not self.active:
            return False  # Do nothing if already hit
        
        self.progress += self.speed
        
        if self.progress > 1.1: # Missed (went past the hit zone)
            self.active = False
            return False # Tell GameManager to remove it
        
        # Check if the target is currently inside the logical hit zone
        self.in_hit_zone = (self.progress >= self.hit_zone_start and 
                            self.progress <= self.hit_zone_end)
        
        return True # Tell GameManager to keep it
    
    def draw(self):
        """Draws the target at its current position and scale"""
        if not self.active:
            return
        
        pos_x, pos_y = self.lane.get_position(self.progress)
        scale_factor = self.lane.get_scale(self.progress)
        size = self.base_size * scale_factor
        
        pushMatrix()
        translate(pos_x, pos_y)
        
        strokeWeight(2 * scale_factor)
        stroke(255)
        
        # Set fill color based on type
        if self.target_type == "red":
            fill(200, 50, 50, 220)
            if self.in_hit_zone:
                fill(255, 100, 100, 255) # Brighter in zone
        elif self.target_type == "blue":
            fill(50, 100, 200, 220)
            if self.in_hit_zone:
                fill(100, 150, 255, 255) # Brighter in zone
        elif self.target_type == "bomb":
            fill(50, 200, 50, 220)
            if self.in_hit_zone:
                fill(100, 255, 100, 255) # Brighter in zone
        
        # Draw the target's main body
        rectMode(CENTER)
        rect(0, 0, size, size, 5 * scale_factor)
        
        # Only draw arrows for "red" and "blue" targets
        if self.target_type != "bomb":
            noFill()
            stroke(255)
            strokeWeight(max(2, 6 * scale_factor))
            draw_arrow(self.direction, size)
        
        popMatrix()
    
    def is_in_hit_zone(self):
        """A simple helper to check if the target is hittable"""
        return self.in_hit_zone
    
    def check_key(self, key_pressed, key_code_pressed):
        """
        Checks if the correct key was pressed for this target.
        """
        if not self.in_hit_zone or not self.active:
            return False
        
        correct = False
        
        # If it's a bomb, *any* key press counts as "correct"
        # (The penalty is handled in the GameManager)
        if self.target_type == "bomb":
            correct = True
        
        # Check Red Targets (Arrow Keys)
        elif self.target_type == "red":
            if (self.direction == "up" and key_code_pressed == UP) or \
               (self.direction == "down" and key_code_pressed == DOWN) or \
               (self.direction == "left" and key_code_pressed == LEFT) or \
               (self.direction == "right" and key_code_pressed == RIGHT):
                correct = True
        
        # Check Blue Targets (WASD)
        elif self.target_type == "blue":
            if (self.direction == "up" and key_pressed == 'w') or \
               (self.direction == "down" and key_pressed == 's') or \
               (self.direction == "left" and key_pressed == 'a') or \
               (self.direction == "right" and key_pressed == 'd'):
                correct = True
        
        # If the key was correct, deactivate the target
        if correct:
            self.active = False
            self.was_hit = True # Set the "memory" that this was hit
        
        return correct

# =========================
# GAME MANAGER CLASS
# =========================
# This is the "brain" of the game.
#
class GameManager:
    def __init__(self):
        # The single vanishing point for all lanes
        self.vp_x = width / 2
        self.vp_y = 50
        
        # --- HIT ZONE ALIGNMENT ---
        self.hit_line_y = height - 80
        self.hit_progress_start = 0.75 # This matches the Target's 0.75
        self.hit_zone_start_y = (self.vp_y + 
                                (self.hit_line_y - self.vp_y) * self.hit_progress_start)
        self.hit_zone_height = self.hit_line_y - self.hit_zone_start_y
        lane_y_bottom = self.hit_line_y

        # Create the 4 lanes
        lane_spacing = 150
        self.lanes = [
            Lane(0, "left", self.vp_x, self.vp_y, 
                 width/2 - lane_spacing * 1.5, lane_y_bottom),
            Lane(1, "down", self.vp_x, self.vp_y, 
                 width/2 - lane_spacing * 0.5, lane_y_bottom),
            Lane(2, "up", self.vp_x, self.vp_y, 
                 width/2 + lane_spacing * 0.5, lane_y_bottom),
            Lane(3, "right", self.vp_x, self.vp_y,
                 width/2 + lane_spacing * 1.5, lane_y_bottom)
        ]
        
        # --- Game state variables ---
        self.targets = []
        self.score = 0
        self.misses = 0
        
        # --- Spawning logic ---
        self.spawn_timer = 0
        self.spawn_interval = 80
        self.min_spawn_interval = 40
        
        # --- Feedback message ("HIT!", "MISS") ---
        self.feedback_timer = 0
        self.feedback_text = ""
        self.feedback_color = color(255)
        
        # --- Difficulty ---
        self.frames_elapsed = 0
        self.difficulty_level = 1
        self.base_target_speed = 0.008
        self.current_target_speed = self.base_target_speed
        
        # --- CHANGE ---
        # Increased this value from 0.0005 to 0.002 to make
        # the speed-up much more noticeable.
        self.speed_increase_amount = 0.002
        
        # --- Game Over State ---
        self.game_over = False
        self.max_misses = 10
    
    def restart_game(self):
        """Resets all game variables to their default state"""
        self.targets = []
        self.score = 0
        self.misses = 0
        self.spawn_timer = 0
        self.spawn_interval = 80
        self.frames_elapsed = 0
        self.difficulty_level = 1
        self.current_target_speed = self.base_target_speed
        self.game_over = False
    
    def update(self):
        """Main update loop, called every frame by draw()"""
        
        # If the game is over, don't update anything
        if self.game_over:
            return
            
        self.frames_elapsed += 1
        
        # Increase difficulty every 600 frames (10 seconds)
        if self.frames_elapsed % 600 == 0:
            self.difficulty_level += 1
            # 1. Targets appear more often
            self.spawn_interval = max(self.min_spawn_interval, 
                                      self.spawn_interval - 5)
            # 2. Targets move faster
            self.current_target_speed += self.speed_increase_amount
        
        # --- Spawn new targets ---
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_target()
        
        # --- Update all targets ---
        for target in reversed(self.targets):
            if not target.update():
                # Target is inactive (hit or missed)
                self.targets.remove(target)
                
                # Check if it was a "miss"
                if (not target.was_hit and 
                    target.progress > target.hit_zone_start and 
                    target.target_type != "bomb"):
                    
                    self.misses += 1
                    self.show_feedback("MISS", color(255, 100, 100))
                    
                    # Check for game over
                    if self.misses >= self.max_misses:
                        self.game_over = True
        
        # Count down the feedback message timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1
    
    def draw(self):
        """Main draw loop, called every frame by draw()"""
        
        # If the game is over, show the game over screen
        if self.game_over:
            self.draw_game_over()
        else:
            # --- Normal Game Draw Logic ---
            
            # Draw all lanes
            for lane in self.lanes:
                lane.draw()
            
            # Draw vanishing point
            fill(255, 255, 0, 150)
            noStroke()
            ellipse(self.vp_x, self.vp_y, 15, 15)
            
            # (The visual hit zone is hidden)
            # self.draw_hit_zone() 
            
            # Draw all active targets
            for target in self.targets:
                target.draw()
            
            # Draw the UI
            self.draw_ui()
    
    def draw_game_over(self):
        """Draws the 'Game Over' screen"""
        fill(200, 0, 0)
        textAlign(CENTER, CENTER)
        textSize(64)
        text("GAME OVER", width/2, height/2 - 50)
        
        textSize(24)
        fill(255)
        text("Final Score: " + str(self.score), width/2, height/2 + 20)
        
        textSize(20)
        fill(200)
        text("Press 'R' to Restart", width/2, height/2 + 70)
    
    def draw_hit_zone(self):
        """Draws the (hidden) hit zone"""
        fill(255, 255, 0, 50)
        noStroke()
        rect(0, self.hit_zone_start_y, width, self.hit_zone_height)
        
        noFill()
        stroke(255, 255, 0, 200)
        strokeWeight(3)
        rect(0, self.hit_zone_start_y, width, self.hit_zone_height)
        
        fill(255, 255, 0, 200)
        textAlign(CENTER, CENTER)
        textSize(20)
        text("HIT ZONE", width/2, self.hit_zone_start_y + self.hit_zone_height/2)
    
    def draw_ui(self):
        """Draws all user interface elements (score, combo, help text)"""
        fill(255)
        textAlign(LEFT, TOP)
        textSize(32)
        text("Score: " + str(self.score), 20, 20)
        
        fill(200)
        textSize(16)
        text("Level: " + str(self.difficulty_level), 20, 65)
        
        fill(255, 100, 100)
        text("Misses: " + str(self.misses) + "/" + str(self.max_misses), 20, 85)
        
        textAlign(RIGHT, TOP)
        textSize(14)
        fill(200, 50, 50)
        text("RED = Arrow Keys", width - 20, 20)
        fill(50, 100, 200)
        text("BLUE = WASD", width - 20, 40)
        
        fill(200)
        textSize(12)
        textAlign(CENTER, TOP)
        text("Press the correct key as targets reach the bottom", 
             width/2, 10)
        
        if self.feedback_timer > 0:
            textAlign(CENTER, CENTER)
            textSize(48)
            alpha = map(self.feedback_timer, 0, 30, 0, 255)
            fill(red(self.feedback_color), green(self.feedback_color), 
                 blue(self.feedback_color), alpha)
            text(self.feedback_text, width/2, height/2 - 100)
    
    def spawn_target(self):
        """Creates a new target on a random lane with a random type"""
        lane = self.lanes[int(random(len(self.lanes)))]
        
        # Add logic for spawning bombs
        roll = random(1)
        if roll < 0.15: # 15% chance for a bomb
            target_type = "bomb"
        else: # 85% chance for a normal note
            # 50/50 split of the remaining 85%
            target_type = "red" if random(1) < 0.5 else "blue"
        
        # Create the new Target object and pass it the CURRENT target speed
        new_target = Target(lane, target_type, self.current_target_speed)
        self.targets.append(new_target)
    
    def check_input(self, key_pressed, key_code_pressed):
        """Handles all key press events."""
        hit_any = False
        
        for target in self.targets:
            if target.check_key(key_pressed, key_code_pressed):
                hit_any = True
                
                # Check if it's a bomb *before* giving points
                if target.target_type == "bomb":
                    self.misses += 3
                    self.show_feedback("BOMB! +3 Misses", color(255, 100, 50))
                    # Check for game over immediately
                    if self.misses >= self.max_misses:
                        self.game_over = True
                else:
                    # --- Regular Hit Logic (NO COMBO) ---
                    points = 10 # Flat 10 points
                    self.score += points
                    self.show_feedback("HIT! +" + str(points), color(100, 255, 100))
                
                break # Stop checking (one hit per key press)
        
        # --- Handle wrong key press ---
        if not hit_any:
            any_in_zone = any(t.is_in_hit_zone() for t in self.targets)
            if any_in_zone:
                self.show_feedback("WRONG KEY!", color(255, 150, 50))
    
    def show_feedback(self, text, col):
        """Helper function to show a feedback message"""
        self.feedback_text = text
        self.feedback_color = col
        self.feedback_timer = 30 # Show for 30 frames

# =========================
# MAIN GAME SETUP
# =========================
game_manager = None

def setup():
    """Runs once at the start of the program"""
    global game_manager
    size(800, 600)
    game_manager = GameManager()

def draw():
    """Runs 60 times per second (the 'game loop')"""
    background(20, 20, 40)
    game_manager.update()
    game_manager.draw()

def keyPressed():
    """Runs once every time a key is pressed"""
    
    # Check if the game is over first
    if game_manager.game_over:
        # If 'r' is pressed, restart the game
        if key == 'r' or key == 'R':
            game_manager.restart_game()
    else:
        # If the game is not over, play normally
        game_manager.check_input(key, keyCode)
