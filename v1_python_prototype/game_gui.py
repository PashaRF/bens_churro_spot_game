import pygame
import sys
import time
import random
import json
import os

# --- Initialize Pygame Engine ---
pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ben's Churro Spot - Interactive Chef Edition")
clock = pygame.time.Clock()

# --- Cohesive Color Palette ---
BG_COLOR = (248, 245, 237)       # Warm Bakery Cream
PANEL_COLOR = (255, 255, 255)    # Clean Card White
TEXT_COLOR = (44, 34, 30)        # Deep Chocolate Brown
ACCENT_COLOR = (212, 140, 70)    # Golden Crisp Churro Brown
BORDER_COLOR = (195, 180, 170)   # Light Muted Taupe
GREEN_BUTTON = (76, 154, 42)     # Success Green
BLUE_BUTTON = (41, 128, 185)     # Deep Interactive Blue
RED_BUTTON = (192, 57, 43)       # Alert Crimson

# --- Typography Layout Setup ---
FONT_TITLE = pygame.font.SysFont("arial", 32, bold=True)
FONT_SUBTITLE = pygame.font.SysFont("arial", 20, bold=True)
FONT_BODY = pygame.font.SysFont("arial", 15, bold=True)
FONT_TICKET = pygame.font.SysFont("couriernew", 14, bold=True)

# --- Save Configuration ---
SAVE_FILE = "savegame.json"

# --- Live Game State Hub ---
game_state = {
    "is_running": True,
    "character_name": "",
    "current_station": "Front Counter",
    "screen_state": "INTRO",
    "intro_stage": "NAME",
    "start_time": 0,
    "money": 0.00,
    "completed_orders": 0,  # Tracks progress towards shift completion

    # Core Game Data Queues
    "tickets": [],
    "waiting_customers": [],
    "prepared_dough_queue": [],
    "finished_plates": [],

    # Multi-Item Active Plate Tracking Node
    "active_plate": {
        "churros": [],
        "sauce": "None",
        "topping": "None",
        "is_locked": False
    },

    "last_arrival_time": 0,
    "arrival_cooldown": 25.0,
    "warning_message": "",
    "warning_timer": 0.0,

    # Station Tracking Map
    "fryers": {
        1: [],
        2: [],
        3: [],
        4: []
    }
}

input_name_buffer = ""

# --- JSON Save & Load Mechanisms ---

def save_game():
    save_data = {
        "character_name": game_state["character_name"],
        "money": game_state["money"],
        "completed_orders": game_state["completed_orders"],
        "tickets": game_state["tickets"],
        "waiting_customers": game_state["waiting_customers"],
        "prepared_dough_queue": game_state["prepared_dough_queue"],
        "finished_plates": game_state["finished_plates"],
        "active_plate": game_state["active_plate"],
        "fryers": game_state["fryers"]
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(save_data, f, indent=4)
    print("Game successfully saved to JSON!")

def load_game():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)

        game_state["character_name"] = data.get("character_name", "Chef")
        game_state["money"] = data.get("money", 0.0)
        game_state["completed_orders"] = data.get("completed_orders", 0)
        game_state["tickets"] = data.get("tickets", [])
        game_state["waiting_customers"] = data.get("waiting_customers", [])
        game_state["prepared_dough_queue"] = data.get("prepared_dough_queue", [])
        game_state["finished_plates"] = data.get("finished_plates", [])
        game_state["active_plate"] = data.get("active_plate", {
            "churros": [], "sauce": "None", "topping": "None", "is_locked": False})

        # Re-map JSON string keys back to Pygame integer keys for the fryers dictionary
        loaded_fryers = data.get("fryers", {"1": [], "2": [], "3": [], "4": []})
        game_state["fryers"] = {int(k): v for k, v in loaded_fryers.items()}
        return True
    return False

# --- Helper Functions for Spawning Live Gameplay Entities ---

def handle_automatic_arrivals():
    if game_state["screen_state"] != "GAME":
        return

    now = time.time()
    if now - game_state["last_arrival_time"] > game_state["arrival_cooldown"]:
        if len(game_state["waiting_customers"]) < 5:
            pool = ["Papa Louie", "Wally", "Penny", "Rita",
                    "Marty", "Big Pauly", "Prudence", "Cooper"]
            chosen_name = random.choice(pool)

            existing_names = [c["name"] for c in game_state["waiting_customers"]
                             ] + [t["customer"] for t in game_state["tickets"]]
            base_name = chosen_name
            suffix_counter = 2

            while chosen_name in existing_names:
                chosen_name = f"{base_name} {suffix_counter}"
                suffix_counter += 1

            game_state["waiting_customers"].append({"name": chosen_name})

        game_state["last_arrival_time"] = now

def update_fryer_timers():
    """Ticks down frying states for all contents across all multi-churro baskets, including burn timers."""
    for f_id, items in game_state["fryers"].items():
        for fryer in items:
            if fryer["status"] == "Frying Side 1":
                fryer["time_left"] -= 1 / 60.0
                if fryer["time_left"] <= 0:
                    fryer["status"] = "Ready to Flip"
                    fryer["time_left"] = 6.0
            elif fryer["status"] == "Ready to Flip":
                fryer["time_left"] -= 1 / 60.0
                if fryer["time_left"] <= 0:
                    fryer["status"] = "Burnt"
            elif fryer["status"] == "Frying Side 2":
                fryer["time_left"] -= 1 / 60.0
                if fryer["time_left"] <= 0:
                    fryer["status"] = "Ready to Collect"
                    fryer["time_left"] = 6.0
            elif fryer["status"] == "Ready to Collect":
                fryer["time_left"] -= 1 / 60.0
                if fryer["time_left"] <= 0:
                    fryer["status"] = "Burnt"

def show_warning(message):
    game_state["warning_message"] = message
    game_state["warning_timer"] = 8.0

# --- Drawing/Rendering Layout Code ---

def draw_intro_screen():
    screen.fill(BG_COLOR)

    header_rect = pygame.Rect(150, 70, 900, 100)
    pygame.draw.rect(screen, PANEL_COLOR, header_rect, border_radius=15)
    pygame.draw.rect(screen, ACCENT_COLOR, header_rect, width=3, border_radius=15)

    title_text = FONT_TITLE.render("--- Welcome to Ben's Churro Spot! ---", True, ACCENT_COLOR)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 98))

    content_rect = pygame.Rect(200, 210, 800, 480)
    pygame.draw.rect(screen, PANEL_COLOR, content_rect, border_radius=15)
    pygame.draw.rect(screen, BORDER_COLOR, content_rect, width=2, border_radius=15)

    if game_state["intro_stage"] == "NAME":
        prompt_lbl = FONT_SUBTITLE.render("Enter your custom character's name:", True, TEXT_COLOR)
        screen.blit(prompt_lbl, (WIDTH // 2 - prompt_lbl.get_width() // 2, 280))

        input_box = pygame.Rect(350, 350, 500, 55)
        pygame.draw.rect(screen, BG_COLOR, input_box, border_radius=8)
        pygame.draw.rect(screen, ACCENT_COLOR if len(
            input_name_buffer) > 0 else BORDER_COLOR, input_box, width=2, border_radius=8)

        cursor = "|" if (time.time() % 1.0 > 0.5) else ""
        name_surf = FONT_SUBTITLE.render(input_name_buffer + cursor, True, TEXT_COLOR)
        screen.blit(name_surf, (input_box.x + 15, input_box.y +
                    (input_box.height // 2 - name_surf.get_height() // 2)))

        if os.path.exists(SAVE_FILE):
            btn_load = pygame.Rect(350, 520, 230, 50)
            pygame.draw.rect(screen, BLUE_BUTTON, btn_load, border_radius=8)
            lbl_load = FONT_SUBTITLE.render("Load Save", True, PANEL_COLOR)
            screen.blit(lbl_load, (btn_load.x + (btn_load.width // 2 - lbl_load.get_width() // 2), btn_load.y + 12))

            btn_continue = pygame.Rect(620, 520, 230, 50)
        else:
            btn_continue = pygame.Rect(500, 520, 200, 50)

        pygame.draw.rect(screen, GREEN_BUTTON if len(
            input_name_buffer.strip()) > 0 else BORDER_COLOR, btn_continue, border_radius=8)
        btn_lbl = FONT_SUBTITLE.render("New Game", True, PANEL_COLOR)
        screen.blit(btn_lbl, (btn_continue.x + (btn_continue.width // 2 - btn_lbl.get_width() // 2), btn_continue.y + 12))

    elif game_state["intro_stage"] == "SPIEL":
        welcome_lbl = FONT_SUBTITLE.render(
            f"Welcome aboard, {game_state['character_name']}!", True, GREEN_BUTTON)
        screen.blit(welcome_lbl, (WIDTH // 2 - welcome_lbl.get_width() // 2, 240))

        spiel_lines = [
            "Here is how it works: You will take orders at the Front Counter,",
            "pipe the dough at the Pastry Station, fry them up at the Fry Station,",
            "add delicious toppings at the Topping Station, and cash them out",
            "at the Pay Counter.",
            "",
            "Keep an eye on your tickets and the clock!"
        ]

        text_y = 300
        for line in spiel_lines:
            line_surf = FONT_SUBTITLE.render(line, True, TEXT_COLOR)
            screen.blit(line_surf, (WIDTH // 2 - line_surf.get_width() // 2, text_y))
            text_y += 35

        btn_start = pygame.Rect(450, 580, 300, 60)
        pygame.draw.rect(screen, ACCENT_COLOR, btn_start, border_radius=10)
        start_lbl = FONT_SUBTITLE.render("START YOUR SHIFT", True, PANEL_COLOR)
        screen.blit(start_lbl, (btn_start.x + (btn_start.width // 2 - start_lbl.get_width() //
                    2), btn_start.y + (btn_start.height // 2 - start_lbl.get_height() // 2)))

def draw_game_screen():
    screen.fill(BG_COLOR)

    # --- HEADER MANAGEMENT PANEL ---
    header_rect = pygame.Rect(20, 15, 1160, 70)
    pygame.draw.rect(screen, PANEL_COLOR, header_rect, border_radius=10)
    pygame.draw.rect(screen, ACCENT_COLOR, header_rect, width=2, border_radius=10)

    chef_surf = FONT_SUBTITLE.render(f"Chef: {game_state['character_name']}", True, TEXT_COLOR)
    screen.blit(chef_surf, (40, 35))

    # Shifted safely left to avoid timer/quit collisions
    money_surf = FONT_SUBTITLE.render(f"Earnings: ${game_state['money']:.2f}", True, GREEN_BUTTON)
    screen.blit(money_surf, (530, 35))

    orders_surf = FONT_SUBTITLE.render(f"Orders: {game_state['completed_orders']}/10", True, BLUE_BUTTON)
    screen.blit(orders_surf, (720, 35))

    btn_save_quit = pygame.Rect(WIDTH - 180, 25, 140, 40)
    pygame.draw.rect(screen, RED_BUTTON, btn_save_quit, border_radius=6)
    lbl_sq = FONT_BODY.render("Save & Quit", True, PANEL_COLOR)
    screen.blit(lbl_sq, (btn_save_quit.x + 15, btn_save_quit.y + 10))

    elapsed = time.time() - game_state["start_time"]
    time_str = f"Time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
    time_surf = FONT_SUBTITLE.render(time_str, True, TEXT_COLOR)
    screen.blit(time_surf, (WIDTH - 210 - time_surf.get_width(), 35))

    # --- LIVE ORDER TICKET RAIL ---
    rail_rect = pygame.Rect(20, 100, 1160, 160)
    pygame.draw.rect(screen, PANEL_COLOR, rail_rect, border_radius=10)
    pygame.draw.rect(screen, BORDER_COLOR, rail_rect, width=1, border_radius=10)

    rail_lbl = FONT_BODY.render("ACTIVE ORDER TICKETS (TAKEN ORDERS)", True, BORDER_COLOR)
    screen.blit(rail_lbl, (35, 105))

    if not game_state["tickets"]:
        empty_lbl = FONT_SUBTITLE.render(
            "[ No active tickets. Head to Front Counter to take customer orders! ]", True, BORDER_COLOR)
        screen.blit(empty_lbl, (WIDTH // 2 - empty_lbl.get_width() // 2, 170))
    else:
        ticket_x = 40
        for idx, t in enumerate(game_state["tickets"][:4]):
            t_box = pygame.Rect(ticket_x, 130, 260, 120)
            pygame.draw.rect(screen, BG_COLOR, t_box, border_radius=6)
            pygame.draw.rect(screen, ACCENT_COLOR if idx == 0 else BORDER_COLOR, t_box, width=2, border_radius=6)

            c_lbl = FONT_TICKET.render(f"Cust: {t['customer']}", True, TEXT_COLOR)
            o_lbl = FONT_TICKET.render(f"Need: {t['qty']}x {t['shape']}", True, TEXT_COLOR)
            s_lbl = FONT_TICKET.render(f"Sauce: {t['sauce']}", True, ACCENT_COLOR)
            p_lbl = FONT_TICKET.render(f"Top: {t['topping']}", True, BLUE_BUTTON)

            screen.blit(c_lbl, (t_box.x + 12, t_box.y + 10))
            screen.blit(o_lbl, (t_box.x + 12, t_box.y + 35))
            screen.blit(s_lbl, (t_box.x + 12, t_box.y + 60))
            screen.blit(p_lbl, (t_box.x + 12, t_box.y + 85))
            ticket_x += 285

    # --- MAIN WORKSPACE SYSTEM AREA ---
    work_rect = pygame.Rect(260, 280, 920, 500)
    pygame.draw.rect(screen, PANEL_COLOR, work_rect, border_radius=12)
    pygame.draw.rect(screen, ACCENT_COLOR, work_rect, width=2, border_radius=12)

    # Left Navigation Sidebar Buttons
    stations_list = ["Front Counter", "Pastry Station", "Fry Station", "Topping Station", "Pay Counter"]
    for idx, name in enumerate(stations_list):
        btn = pygame.Rect(20, 280 + (idx * 75), 220, 60)
        is_active = (game_state["current_station"] == name)
        pygame.draw.rect(screen, ACCENT_COLOR if is_active else PANEL_COLOR, btn, border_radius=8)
        pygame.draw.rect(screen, ACCENT_COLOR, btn, width=2, border_radius=8)

        lbl = FONT_SUBTITLE.render(name, True, PANEL_COLOR if is_active else TEXT_COLOR)
        screen.blit(lbl, (btn.x + (btn.width // 2 - lbl.get_width() // 2),
                    btn.y + (btn.height // 2 - lbl.get_height() // 2)))

    # --- STATION RENDERING INTERACTIVITY ---
    current = game_state["current_station"]

    if current == "Front Counter":
        list_box = pygame.Rect(290, 310, 420, 440)
        pygame.draw.rect(screen, BG_COLOR, list_box, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, list_box, width=1, border_radius=8)
        screen.blit(FONT_SUBTITLE.render("Lobby Waiting Line:", True, TEXT_COLOR), (310, 325))

        if not game_state["waiting_customers"]:
            screen.blit(FONT_BODY.render("Lobby is clear. Waiting for arrivals...", True, BORDER_COLOR), (310, 370))
        else:
            for c_idx, cust in enumerate(game_state["waiting_customers"][:6]):
                row_y = 370 + (c_idx * 60)
                row_rect = pygame.Rect(310, row_y, 380, 50)
                pygame.draw.rect(screen, PANEL_COLOR, row_rect, border_radius=6)
                pygame.draw.rect(screen, BORDER_COLOR, row_rect, width=1, border_radius=6)

                info_txt = f"{cust['name']} - Waiting to Order"
                screen.blit(FONT_BODY.render(info_txt, True, TEXT_COLOR), (325, row_y + 15))

        action_box = pygame.Rect(740, 310, 420, 440)
        pygame.draw.rect(screen, BG_COLOR, action_box, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, action_box, width=1, border_radius=8)
        screen.blit(FONT_SUBTITLE.render("Order Window Desk:", True, TEXT_COLOR), (760, 325))

        if game_state["waiting_customers"]:
            active_customer = game_state["waiting_customers"][0]
            msg_line1 = f"Customer up next: {active_customer['name']}"
            screen.blit(FONT_BODY.render(msg_line1, True, TEXT_COLOR), (760, 380))
            screen.blit(FONT_BODY.render("Click below to write down their order card.", True, BORDER_COLOR), (760, 410))

            btn_take = pygame.Rect(760, 460, 380, 65)
            pygame.draw.rect(screen, GREEN_BUTTON, btn_take, border_radius=8)
            lbl = FONT_SUBTITLE.render("TAKE ORDER SLIP", True, PANEL_COLOR)
            screen.blit(lbl, (btn_take.x + (btn_take.width // 2 - lbl.get_width() // 2), btn_take.y + 20))
        else:
            screen.blit(FONT_BODY.render("No customers at the register counter.", True, BORDER_COLOR), (760, 380))
            screen.blit(FONT_BODY.render("New arrivals are now tightly regulated.", True, ACCENT_COLOR), (760, 410))

    elif current == "Pastry Station":
        screen.blit(FONT_SUBTITLE.render("Choose a Shape Component to Pipe into the Tray:", True, TEXT_COLOR), (290, 310))

        shapes = ["Straight", "Loop", "Spiral"]
        for idx, shp in enumerate(shapes):
            btn_pipe = pygame.Rect(290 + (idx * 290), 360, 260, 80)
            pygame.draw.rect(screen, ACCENT_COLOR, btn_pipe, border_radius=8)
            lbl = FONT_SUBTITLE.render(f"Pipe {shp}", True, PANEL_COLOR)
            screen.blit(lbl, (btn_pipe.x + (btn_pipe.width // 2 - lbl.get_width() // 2),
                        btn_pipe.y + (btn_pipe.height // 2 - lbl.get_height() // 2)))

        tray_box = pygame.Rect(290, 480, 860, 270)
        pygame.draw.rect(screen, BG_COLOR, tray_box, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, tray_box, width=1, border_radius=8)
        screen.blit(FONT_SUBTITLE.render("Prepared Tray Queue (Ready to Fry):", True, TEXT_COLOR), (310, 495))

        if not game_state["prepared_dough_queue"]:
            screen.blit(FONT_BODY.render("Tray is empty. Pipe dough shapes above to fill it.", True, BORDER_COLOR), (310, 540))
        else:
            for d_idx, shp in enumerate(game_state["prepared_dough_queue"][:15]):
                gx = 310 + (d_idx % 5 * 165)
                gy = 540 + (d_idx // 5 * 60)
                box = pygame.Rect(gx, gy, 150, 50)
                pygame.draw.rect(screen, PANEL_COLOR, box, border_radius=4)
                pygame.draw.rect(screen, BORDER_COLOR, box, 1, border_radius=4)
                screen.blit(FONT_BODY.render(f"{shp}", True, TEXT_COLOR), (gx + 15, gy + 15))

    elif current == "Fry Station":
        screen.blit(FONT_SUBTITLE.render("Deep Fryer Grid (Each Basket Holds Up to 2 Churros Simultaneously):", True, TEXT_COLOR), (290, 310))

        for f_id in range(1, 5):
            col = (f_id - 1) % 2
            row = (f_id - 1) // 2
            fx = 290 + (col * 440)
            fy = 350 + (row * 205)

            f_box = pygame.Rect(fx, fy, 410, 185)
            pygame.draw.rect(screen, BG_COLOR, f_box, border_radius=8)
            pygame.draw.rect(screen, BORDER_COLOR, f_box, width=1, border_radius=8)

            items = game_state["fryers"][f_id]
            screen.blit(FONT_SUBTITLE.render(f"Basket #{f_id} ({len(items)}/2 Filled)", True, TEXT_COLOR), (fx + 15, fy + 10))

            s1_rect = pygame.Rect(fx + 15, fy + 40, 380, 60)
            s2_rect = pygame.Rect(fx + 15, fy + 110, 380, 60)
            slots = [(s1_rect, 0), (s2_rect, 1)]

            for s_rect, idx in slots:
                if idx < len(items):
                    churro = items[idx]
                    if churro["status"] == "Frying Side 1":
                        pygame.draw.rect(screen, PANEL_COLOR, s_rect, border_radius=6)
                        pygame.draw.rect(screen, BORDER_COLOR, s_rect, width=1, border_radius=6)
                        lbl_txt = f"{churro['shape']}: Side 1 ({max(0.0, churro['time_left']):.1f}s)"
                        lbl_color = TEXT_COLOR
                    elif churro["status"] == "Ready to Flip":
                        pygame.draw.rect(screen, ACCENT_COLOR, s_rect, border_radius=6)
                        lbl_txt = f"FLIP {churro['shape'].upper()} (Burns in {max(0.0, churro['time_left']):.1f}s)"
                        lbl_color = PANEL_COLOR
                    elif churro["status"] == "Frying Side 2":
                        pygame.draw.rect(screen, PANEL_COLOR, s_rect, border_radius=6)
                        pygame.draw.rect(screen, BORDER_COLOR, s_rect, width=1, border_radius=6)
                        lbl_txt = f"{churro['shape']}: Side 2 ({max(0.0, churro['time_left']):.1f}s)"
                        lbl_color = TEXT_COLOR
                    elif churro["status"] == "Ready to Collect":
                        pygame.draw.rect(screen, GREEN_BUTTON, s_rect, border_radius=6)
                        lbl_txt = f"COLLECT {churro['shape'].upper()} (Burns in {max(0.0, churro['time_left']):.1f}s)"
                        lbl_color = PANEL_COLOR
                    elif churro["status"] == "Burnt":
                        pygame.draw.rect(screen, RED_BUTTON, s_rect, border_radius=6)
                        lbl_txt = f"TRASH BURNT {churro['shape'].upper()}"
                        lbl_color = PANEL_COLOR

                    surf = FONT_BODY.render(lbl_txt, True, lbl_color)
                    screen.blit(surf, (s_rect.x + 15, s_rect.y + (s_rect.height // 2 - surf.get_height() // 2)))
                else:
                    if idx == len(items) and game_state["prepared_dough_queue"]:
                        pygame.draw.rect(screen, BLUE_BUTTON, s_rect, border_radius=6)
                        lbl_txt = f"Drop {game_state['prepared_dough_queue'][0]}"
                        lbl_color = PANEL_COLOR
                    else:
                        pygame.draw.rect(screen, PANEL_COLOR, s_rect, border_radius=6)
                        pygame.draw.rect(screen, BORDER_COLOR, s_rect, width=1, border_radius=6)
                        lbl_txt = "[ Empty Slot ]"
                        lbl_color = BORDER_COLOR

                    surf = FONT_BODY.render(lbl_txt, True, lbl_color)
                    screen.blit(surf, (s_rect.x + (s_rect.width // 2 - surf.get_width() // 2),
                                       s_rect.y + (s_rect.height // 2 - surf.get_height() // 2)))

    elif current == "Topping Station":
        screen.blit(FONT_SUBTITLE.render("1. Apply Sauce Options", True, TEXT_COLOR), (290, 310))
        sauces = ["None", "Chocolate", "Caramel", "Condensed Milk"]
        for idx, s in enumerate(sauces):
            btn_s = pygame.Rect(290, 350 + (idx * 55), 240, 48)
            is_sel = (game_state["active_plate"]["sauce"] == s)

            pygame.draw.rect(screen, ACCENT_COLOR if is_sel else PANEL_COLOR, btn_s, border_radius=6)
            pygame.draw.rect(screen, ACCENT_COLOR if is_sel else BORDER_COLOR, btn_s, width=2, border_radius=6)

            lbl_s = FONT_BODY.render(s, True, PANEL_COLOR if is_sel else TEXT_COLOR)
            screen.blit(lbl_s, (btn_s.x + 20, btn_s.y + (btn_s.height // 2 - lbl_s.get_height() // 2)))

        screen.blit(FONT_SUBTITLE.render("2. Shake Topping Options", True, TEXT_COLOR), (570, 310))
        toppings = ["None", "Cinnamon Sugar", "Sprinkles", "Crushed Oreos"]
        for idx, t in enumerate(toppings):
            btn_t = pygame.Rect(570, 350 + (idx * 55), 240, 48)
            is_sel = (game_state["active_plate"]["topping"] == t)

            pygame.draw.rect(screen, BLUE_BUTTON if is_sel else PANEL_COLOR, btn_t, border_radius=6)
            pygame.draw.rect(screen, BLUE_BUTTON if is_sel else BORDER_COLOR, btn_t, width=2, border_radius=6)

            lbl_t = FONT_BODY.render(t, True, PANEL_COLOR if is_sel else TEXT_COLOR)
            screen.blit(lbl_t, (btn_t.x + 20, btn_t.y + (btn_t.height // 2 - lbl_t.get_height() // 2)))

        # Column 3: Active Prep Workbench Area
        p_box = pygame.Rect(850, 310, 310, 320)
        pygame.draw.rect(screen, BG_COLOR, p_box, border_radius=6)
        screen.blit(FONT_SUBTITLE.render("3. Workbench", True, TEXT_COLOR), (870, 325))

        workbench_lines = [
            f"Sauce: {game_state['active_plate']['sauce']}",
            f"Topping: {game_state['active_plate']['topping']}",
            f"Churros stacked: {len(game_state['active_plate']['churros'])}"
        ]

        if game_state["active_plate"]["churros"]:
            counts = {}
            for item in game_state["active_plate"]["churros"]:
                counts[item] = counts.get(item, 0) + 1
            for shape_name, qty in counts.items():
                workbench_lines.append(f"  * {qty}x {shape_name}")
        else:
            workbench_lines.append("  * (Plate is empty)")

        ly = 365
        for line in workbench_lines:
            screen.blit(FONT_BODY.render(line, True, TEXT_COLOR), (870, ly))
            ly += 26

        btn_undo = pygame.Rect(870, 520, 270, 35)
        if game_state["active_plate"]["churros"] and not game_state["active_plate"]["is_locked"]:
            pygame.draw.rect(screen, RED_BUTTON, btn_undo, border_radius=8)
            lbl_undo = FONT_BODY.render("Remove Last Churro", True, PANEL_COLOR)
            screen.blit(lbl_undo, (btn_undo.x + (btn_undo.width // 2 - lbl_undo.get_width() // 2), btn_undo.y + 8))

        btn_build = pygame.Rect(870, 565, 270, 50)
        has_items = len(game_state["active_plate"]["churros"]) > 0
        is_locked = game_state["active_plate"]["is_locked"]

        btn_color = BORDER_COLOR if not has_items else (ACCENT_COLOR if is_locked else GREEN_BUTTON)
        pygame.draw.rect(screen, btn_color, btn_build, border_radius=8)

        status_lbl = "Locked & Ready" if is_locked else "Coat & Lock Plate"
        lbl_b = FONT_SUBTITLE.render(status_lbl, True, PANEL_COLOR)
        screen.blit(lbl_b, (btn_build.x + (btn_build.width // 2 - lbl_b.get_width() // 2), btn_build.y + 14))

        inv_box = pygame.Rect(290, 650, 870, 110)
        pygame.draw.rect(screen, BG_COLOR, inv_box, border_radius=6)
        pygame.draw.rect(screen, BORDER_COLOR, inv_box, 1, border_radius=6)
        screen.blit(FONT_SUBTITLE.render("Fried Churros Bin (Click items to pile them onto the plate):", True, TEXT_COLOR), (310, 662))

        if not game_state["finished_plates"]:
            screen.blit(FONT_BODY.render("Bin is empty. Fry and collect items at the Fry Station first.", True, BORDER_COLOR), (310, 705))
        else:
            for p_idx, plate in enumerate(game_state["finished_plates"][:6]):
                p_rect = pygame.Rect(310 + (p_idx * 140), 700, 120, 45)
                pygame.draw.rect(screen, PANEL_COLOR, p_rect, border_radius=4)
                pygame.draw.rect(screen, BORDER_COLOR, p_rect, 1, border_radius=4)
                screen.blit(FONT_BODY.render(f"{plate['shape']}", True, TEXT_COLOR), (p_rect.x + 15, p_rect.y + 14))

    elif current == "Pay Counter":
        screen.blit(FONT_SUBTITLE.render("Order Cashout Terminal & Quality Control Match:", True, TEXT_COLOR), (290, 310))

        invoice_card = pygame.Rect(290, 350, 860, 260)
        pygame.draw.rect(screen, BG_COLOR, invoice_card, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, invoice_card, 1, border_radius=8)

        if not game_state["tickets"]:
            screen.blit(FONT_SUBTITLE.render("No orders available to cash out.", True, BORDER_COLOR), (340, 460))
        else:
            active_ticket = game_state["tickets"][0]
            plate = game_state["active_plate"]

            screen.blit(FONT_SUBTITLE.render(f"Serving Customer: {active_ticket['customer']}", True, ACCENT_COLOR), (320, 370))
            spec_txt = f"Target Recipe: {active_ticket['qty']}x {active_ticket['shape']} with [{active_ticket['sauce']}] + [{active_ticket['topping']}]"
            screen.blit(FONT_BODY.render(spec_txt, True, TEXT_COLOR), (320, 415))

            churros_on_plate = plate["churros"]
            match_qty = (len(churros_on_plate) == active_ticket["qty"])
            match_shape = all(s == active_ticket["shape"] for s in churros_on_plate) if churros_on_plate else False
            match_sauce = (plate["sauce"] == active_ticket["sauce"])
            match_top = (plate["topping"] == active_ticket["topping"])

            q_verif = f"Quantity: {len(churros_on_plate)} / {active_ticket['qty']} " + ("OK" if match_qty else "X")
            sh_verif = "Shape Type Match: " + ("OK" if match_shape else "X")
            s_verif = f"Sauce Coating: {plate['sauce']} " + ("OK" if match_sauce else f"X (Expected {active_ticket['sauce']})")
            t_verif = f"Topping Shaker: {plate['topping']} " + ("OK" if match_top else f"X (Expected {active_ticket['topping']})")

            screen.blit(FONT_BODY.render(q_verif, True, GREEN_BUTTON if match_qty else RED_BUTTON), (320, 460))
            screen.blit(FONT_BODY.render(sh_verif, True, GREEN_BUTTON if match_shape else RED_BUTTON), (320, 488))
            screen.blit(FONT_BODY.render(s_verif, True, GREEN_BUTTON if match_sauce else RED_BUTTON), (320, 516))
            screen.blit(FONT_BODY.render(t_verif, True, GREEN_BUTTON if match_top else RED_BUTTON), (320, 544))

            btn_pay = pygame.Rect(290, 640, 860, 70)
            pygame.draw.rect(screen, GREEN_BUTTON if plate["is_locked"] else BORDER_COLOR, btn_pay, border_radius=10)
            lbl_p = FONT_TITLE.render("SERVE PLATE & COLLECT PAYMENT", True, PANEL_COLOR)
            screen.blit(lbl_p, (btn_pay.x + (btn_pay.width // 2 - lbl_p.get_width() // 2), btn_pay.y + 15))

    # --- WARNING TOAST OVERLAY ---
    if game_state["warning_timer"] > 0:
        warn_surf = FONT_SUBTITLE.render(game_state["warning_message"], True, PANEL_COLOR)
        warn_bg = pygame.Rect(WIDTH // 2 - warn_surf.get_width() // 2 - 20, 720, warn_surf.get_width() + 40, 44)
        pygame.draw.rect(screen, RED_BUTTON, warn_bg, border_radius=8)
        screen.blit(warn_surf, (warn_bg.x + 20, warn_bg.y + 10))

def draw_ending_screen():
    screen.fill(BG_COLOR)

    panel_rect = pygame.Rect(200, 150, 800, 500)
    pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=15)

    if game_state["money"] < 180.00:
        pygame.draw.rect(screen, RED_BUTTON, panel_rect, width=4, border_radius=15)
        title_lbl = FONT_TITLE.render("SHIFT OVER - YOU ARE FIRED!", True, RED_BUTTON)
        msg1 = FONT_SUBTITLE.render(f"Chef {game_state['character_name']}, your earnings were too low (${game_state['money']:.2f}).", True, TEXT_COLOR)
        msg2 = FONT_SUBTITLE.render("Incorrect orders and slow preparation speeds ruined our reputation!", True, TEXT_COLOR)
    else:
        pygame.draw.rect(screen, GREEN_BUTTON, panel_rect, width=4, border_radius=15)
        title_lbl = FONT_TITLE.render("SHIFT OVER - RETIRE IN GLORY!", True, GREEN_BUTTON)
        msg1 = FONT_SUBTITLE.render(f"Outstanding execution, Chef {game_state['character_name']}!", True, TEXT_COLOR)
        msg2 = FONT_SUBTITLE.render(f"With safe operations and massive tips, you earned ${game_state['money']:.2f}!", True, TEXT_COLOR)

    screen.blit(title_lbl, (WIDTH // 2 - title_lbl.get_width() // 2, 200))
    screen.blit(msg1, (WIDTH // 2 - msg1.get_width() // 2, 290))
    screen.blit(msg2, (WIDTH // 2 - msg2.get_width() // 2, 340))

    final_lbl = FONT_TITLE.render(f"Total Shift Earnings: ${game_state['money']:.2f}", True, ACCENT_COLOR)
    screen.blit(final_lbl, (WIDTH // 2 - final_lbl.get_width() // 2, 420))

    btn_menu = pygame.Rect(450, 540, 300, 60)
    pygame.draw.rect(screen, BLUE_BUTTON, btn_menu, border_radius=10)
    lbl_menu = FONT_SUBTITLE.render("PLAY ANOTHER SHIFT", True, PANEL_COLOR)
    screen.blit(lbl_menu, (btn_menu.x + (btn_menu.width // 2 - lbl_menu.get_width() // 2),
                           btn_menu.y + (btn_menu.height // 2 - lbl_menu.get_height() // 2)))

# --- INTERACTIVE CLICK REACTION HANDLER HUB ---

def handle_gameplay_clicks(mx, my):
    # Process Save & Quit
    btn_save_quit = pygame.Rect(WIDTH - 180, 25, 140, 40)
    if btn_save_quit.collidepoint((mx, my)):
        save_game()
        game_state["is_running"] = False
        return

    stations_list = ["Front Counter", "Pastry Station", "Fry Station", "Topping Station", "Pay Counter"]
    for idx, name in enumerate(stations_list):
        btn = pygame.Rect(20, 280 + (idx * 75), 220, 60)
        if btn.collidepoint((mx, my)):
            game_state["current_station"] = name
            return

    current = game_state["current_station"]

    if current == "Front Counter":
        if game_state["waiting_customers"]:
            btn_take = pygame.Rect(760, 460, 380, 65)
            if btn_take.collidepoint((mx, my)):
                customer_data = game_state["waiting_customers"].pop(0)
                shapes = ["Straight", "Loop", "Spiral"]
                sauces = ["Chocolate", "Caramel", "Condensed Milk"]
                toppings = ["Cinnamon Sugar", "Sprinkles", "Crushed Oreos"]

                new_ticket = {
                    "id": len(game_state["tickets"]) + 1,
                    "customer": customer_data["name"],
                    "shape": random.choice(shapes),
                    "qty": random.randint(2, 4),
                    "sauce": random.choice(sauces),
                    "topping": random.choice(toppings),
                    "created_time": time.time()  # Timestamp to benchmark tip deduction
                }
                game_state["tickets"].append(new_ticket)

    elif current == "Pastry Station":
        shapes = ["Straight", "Loop", "Spiral"]
        for idx, shp in enumerate(shapes):
            btn_pipe = pygame.Rect(290 + (idx * 290), 360, 260, 80)
            if btn_pipe.collidepoint((mx, my)):
                if len(game_state["prepared_dough_queue"]) >= 15:
                    show_warning("No space left!")
                else:
                    game_state["prepared_dough_queue"].append(shp)
                return

    elif current == "Fry Station":
        for f_id in range(1, 5):
            col = (f_id - 1) % 2
            row = (f_id - 1) // 2
            fx = 290 + (col * 440)
            fy = 350 + (row * 205)

            s1_rect = pygame.Rect(fx + 15, fy + 40, 380, 60)
            s2_rect = pygame.Rect(fx + 15, fy + 110, 380, 60)
            items = game_state["fryers"][f_id]

            if s1_rect.collidepoint((mx, my)):
                if len(items) >= 1:
                    churro = items[0]
                    if churro["status"] == "Ready to Flip":
                        churro["status"] = "Frying Side 2"
                        churro["time_left"] = 25.0
                    elif churro["status"] == "Ready to Collect":
                        if len(game_state["finished_plates"]) >= 6:
                            show_warning("Bench is full!")
                        else:
                            game_state["finished_plates"].append({"shape": churro["shape"]})
                            items.pop(0)
                    elif churro["status"] == "Burnt":
                        items.pop(0)
                elif len(items) == 0 and game_state["prepared_dough_queue"]:
                    next_dough = game_state["prepared_dough_queue"].pop(0)
                    items.append({"status": "Frying Side 1", "shape": next_dough, "time_left": 25.0})
                return

            if s2_rect.collidepoint((mx, my)):
                if len(items) == 2:
                    churro = items[1]
                    if churro["status"] == "Ready to Flip":
                        churro["status"] = "Frying Side 2"
                        churro["time_left"] = 25.0
                    elif churro["status"] == "Ready to Collect":
                        if len(game_state["finished_plates"]) >= 6:
                            show_warning("Bench is full!")
                        else:
                            game_state["finished_plates"].append({"shape": churro["shape"]})
                            items.pop(1)
                    elif churro["status"] == "Burnt":
                        items.pop(1)
                elif len(items) == 1 and game_state["prepared_dough_queue"]:
                    next_dough = game_state["prepared_dough_queue"].pop(0)
                    items.append({"status": "Frying Side 1", "shape": next_dough, "time_left": 25.0})
                return

    elif current == "Topping Station":
        sauces = ["None", "Chocolate", "Caramel", "Condensed Milk"]
        for idx, s in enumerate(sauces):
            btn_s = pygame.Rect(290, 350 + (idx * 55), 240, 48)
            if btn_s.collidepoint((mx, my)):
                game_state["active_plate"]["sauce"] = s
                return

        toppings = ["None", "Cinnamon Sugar", "Sprinkles", "Crushed Oreos"]
        for idx, t in enumerate(toppings):
            btn_t = pygame.Rect(570, 350 + (idx * 55), 240, 48)
            if btn_t.collidepoint((mx, my)):
                game_state["active_plate"]["topping"] = t
                return

        if game_state["finished_plates"]:
            for p_idx, plate in enumerate(game_state["finished_plates"][:6]):
                p_rect = pygame.Rect(310 + (p_idx * 140), 700, 120, 45)
                if p_rect.collidepoint((mx, my)) and not game_state["active_plate"]["is_locked"]:
                    if len(game_state["active_plate"]["churros"]) >= 6:
                        show_warning("No space left!")
                        return
                    else:
                        game_state["active_plate"]["churros"].append(plate["shape"])
                        game_state["finished_plates"].pop(p_idx)
                        return

        btn_undo = pygame.Rect(870, 520, 270, 35)
        if btn_undo.collidepoint((mx, my)) and game_state["active_plate"]["churros"] and not game_state["active_plate"]["is_locked"]:
            removed_churro = game_state["active_plate"]["churros"].pop()
            game_state["finished_plates"].append({"shape": removed_churro})
            return

        btn_build = pygame.Rect(870, 565, 270, 50)
        if btn_build.collidepoint((mx, my)) and game_state["active_plate"]["churros"]:
            game_state["active_plate"]["is_locked"] = True
            return

    elif current == "Pay Counter":
        if game_state["tickets"]:
            btn_pay = pygame.Rect(290, 640, 860, 70)
            if btn_pay.collidepoint((mx, my)) and game_state["active_plate"]["is_locked"]:
                active_ticket = game_state["tickets"].pop(0)
                
                # --- Advanced Quality Control Vector Calculations ---
                plate = game_state["active_plate"]
                churros_on_plate = plate["churros"]
                
                match_qty = (len(churros_on_plate) == active_ticket["qty"])
                match_shape = all(s == active_ticket["shape"] for s in churros_on_plate) if churros_on_plate else False
                match_sauce = (plate["sauce"] == active_ticket["sauce"])
                match_top = (plate["topping"] == active_ticket["topping"])

                # --- Tip Matrix Calculus Node ---
                tip = 10.00
                if not match_qty: tip -= 2.50
                if not match_shape: tip -= 2.50
                if not match_sauce: tip -= 2.50
                if not match_top: tip -= 2.50

                # --- Time Penalty Logic Calculations ---
                time_taken = time.time() - active_ticket.get("created_time", time.time())
                if time_taken > 60.0:
                    time_penalty = (time_taken - 60.0) * 0.10  # Lose 10 cents per second late
                    tip -= time_penalty

                base_payout = 12.50
                total_order_earnings = base_payout + tip
                if total_order_earnings < 0.0: 
                    total_order_earnings = 0.0  # Floor cap limits negative losses

                game_state["money"] += total_order_earnings
                game_state["completed_orders"] += 1

                show_warning(f"Served! Earned: ${total_order_earnings:.2f} (Tip: ${max(0.0, tip):.2f})")

                # Operational Reset for subsequent tickets
                game_state["active_plate"] = {
                    "churros": [],
                    "sauce": "None",
                    "topping": "None",
                    "is_locked": False
                }

                # Evaluate Shift End Requirement Conditions
                if game_state["completed_orders"] >= 10:
                    game_state["screen_state"] = "ENDING"
                return

# --- MAIN EXECUTION GAME LOOP ---

def main():
    global input_name_buffer
    game_state["start_time"] = time.time()
    game_state["last_arrival_time"] = time.time()

    while game_state["is_running"]:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()

        # Process Pygame Event Bus Queue Node
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state["is_running"] = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_state["screen_state"] == "INTRO":
                        if game_state["intro_stage"] == "NAME":
                            if os.path.exists(SAVE_FILE):
                                btn_load = pygame.Rect(350, 520, 230, 50)
                                btn_continue = pygame.Rect(620, 520, 230, 50)
                                if btn_load.collidepoint((mx, my)):
                                    if load_game():
                                        game_state["screen_state"] = "GAME"
                                elif btn_continue.collidepoint((mx, my)) and len(input_name_buffer.strip()) > 0:
                                    game_state["character_name"] = input_name_buffer.strip()
                                    game_state["intro_stage"] = "SPIEL"
                            else:
                                btn_continue = pygame.Rect(500, 520, 200, 50)
                                if btn_continue.collidepoint((mx, my)) and len(input_name_buffer.strip()) > 0:
                                    game_state["character_name"] = input_name_buffer.strip()
                                    game_state["intro_stage"] = "SPIEL"
                        elif game_state["intro_stage"] == "SPIEL":
                            btn_start = pygame.Rect(450, 580, 300, 60)
                            if btn_start.collidepoint((mx, my)):
                                game_state["screen_state"] = "GAME"
                                game_state["start_time"] = time.time()
                    elif game_state["screen_state"] == "GAME":
                        handle_gameplay_clicks(mx, my)
                    elif game_state["screen_state"] == "ENDING":
                        btn_menu = pygame.Rect(450, 540, 300, 60)
                        if btn_menu.collidepoint((mx, my)):
                            # Full system initialization flush wipe to restart fresh game loop
                            game_state["money"] = 0.0
                            game_state["completed_orders"] = 0
                            game_state["tickets"] = []
                            game_state["waiting_customers"] = []
                            game_state["prepared_dough_queue"] = []
                            game_state["finished_plates"] = []
                            game_state["active_plate"] = {"churros": [], "sauce": "None", "topping": "None", "is_locked": False}
                            game_state["fryers"] = {1: [], 2: [], 3: [], 4: []}
                            input_name_buffer = ""
                            game_state["screen_state"] = "INTRO"
                            game_state["intro_stage"] = "NAME"

            elif event.type == pygame.KEYDOWN:
                if game_state["screen_state"] == "INTRO" and game_state["intro_stage"] == "NAME":
                    if event.key == pygame.K_RETURN:
                        if len(input_name_buffer.strip()) > 0:
                            game_state["character_name"] = input_name_buffer.strip()
                            game_state["intro_stage"] = "SPIEL"
                    elif event.key == pygame.K_BACKSPACE:
                        input_name_buffer = input_name_buffer[:-1]
                    else:
                        if len(input_name_buffer) < 30 or event.unicode == ' ':
                            input_name_buffer += event.unicode

        # Engine Physics Tick Simulation Matrix Updates
        if game_state["screen_state"] == "GAME":
            handle_automatic_arrivals()
            update_fryer_timers()
            if game_state["warning_timer"] > 0:
                game_state["warning_timer"] -= 1 / 60.0

        # Draw Output Surface Context Buffers
        if game_state["screen_state"] == "INTRO":
            draw_intro_screen()
        elif game_state["screen_state"] == "GAME":
            draw_game_screen()
        elif game_state["screen_state"] == "ENDING":
            draw_ending_screen()

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()