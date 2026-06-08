import pygame
import sys
import time
import random

# --- Initialize Pygame Engine ---
pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🥞 Ben's Churro Spot - Interactive Chef Edition")
clock = pygame.time.Clock()

# --- Cohesive Color Palette ---
BG_COLOR = (248, 245, 237)       # Warm Bakery Cream
PANEL_COLOR = (255, 255, 255)    # Clean Card White
TEXT_COLOR = (44, 34, 30)        # Deep Chocolate Brown
ACCENT_COLOR = (212, 140, 70)    # Golden Crisp Churro Brown
BORDER_COLOR = (195, 180, 170)    # Light Muted Taupe
GREEN_BUTTON = (76, 154, 42)     # Success Green
BLUE_BUTTON = (41, 128, 185)     # Deep Interactive Blue
RED_BUTTON = (192, 57, 43)       # Alert Crimson

# --- Typography Layout Setup ---
FONT_TITLE = pygame.font.SysFont("arial", 32, bold=True)
FONT_SUBTITLE = pygame.font.SysFont("arial", 20, bold=True)
FONT_BODY = pygame.font.SysFont("arial", 15, bold=True)
FONT_TICKET = pygame.font.SysFont("couriernew", 14, bold=True)

# --- Live Game State Hub ---
game_state = {
    "is_running": True,
    "character_name": "",
    "current_station": "Front Counter",
    "screen_state": "INTRO", 
    "intro_stage": "NAME",   
    "start_time": 0,
    "money": 0.00,
    
    # Core Game Data Queues
    "tickets": [],
    "waiting_customers": [],          
    "prepared_dough_queue": [],
    "finished_plates": [],             # Acts as the Fried Churro Bin waiting processing
    
    # Multi-Item Active Plate Tracking Node
    "active_plate": {
        "churros": [],                 # Array supporting multiple items (e.g., ["Straight", "Straight"])
        "sauce": "None",
        "topping": "None",
        "is_locked": False
    },
    
    # Automated Customer Arrival Rate
    "last_arrival_time": 0,
    "arrival_cooldown": 25.0,         
    
    # Station Tracking Map Supporting 2 Churros per Fryer Basket
    "fryers": {
        1: [],  # Holds active item dictionaries: {"status": "Frying Side 1", "shape": "...", "time_left": X}
        2: [],
        3: [],
        4: []
    }
}

input_name_buffer = ""

# --- Helper Functions for Spawning Live Gameplay Entities ---
def handle_automatic_arrivals():
    """Tracks system delta time to automatically walk customers into the lobby box."""
    if game_state["screen_state"] != "GAME":
        return
        
    now = time.time()
    if now - game_state["last_arrival_time"] > game_state["arrival_cooldown"]:
        if len(game_state["waiting_customers"]) < 5:
            pool = ["Papa Louie", "Wally", "Penny", "Rita", "Marty", "Big Pauly", "Prudence", "Cooper"]
            chosen_name = random.choice(pool)
            game_state["waiting_customers"].append({"name": chosen_name})
            
        game_state["last_arrival_time"] = now

def update_fryer_timers():
    """Ticks down frying states for all contents across all multi-churro baskets."""
    for f_id, items in game_state["fryers"].items():
        for fryer in items:
            if fryer["status"] == "Frying Side 1":
                fryer["time_left"] -= 1 / 60.0
                if fryer["time_left"] <= 0:
                    fryer["status"] = "Ready to Flip"
                    fryer["time_left"] = 8.0  
            elif fryer["status"] == "Frying Side 2":
                fryer["time_left"] -= 1 / 60.0
                if fryer["time_left"] <= 0:
                    fryer["status"] = "Ready to Collect"

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
        pygame.draw.rect(screen, ACCENT_COLOR if len(input_name_buffer) > 0 else BORDER_COLOR, input_box, width=2, border_radius=8)
        
        cursor = "|" if (time.time() % 1.0 > 0.5) else ""
        name_surf = FONT_SUBTITLE.render(input_name_buffer + cursor, True, TEXT_COLOR)
        screen.blit(name_surf, (input_box.x + 15, input_box.y + (input_box.height // 2 - name_surf.get_height() // 2)))
        
        btn_continue = pygame.Rect(500, 520, 200, 50)
        pygame.draw.rect(screen, GREEN_BUTTON if len(input_name_buffer.strip()) > 0 else BORDER_COLOR, btn_continue, border_radius=8)
        btn_lbl = FONT_SUBTITLE.render("Continue", True, PANEL_COLOR)
        screen.blit(btn_lbl, (btn_continue.x + (btn_continue.width // 2 - btn_lbl.get_width() // 2), btn_continue.y + (btn_continue.height // 2 - btn_lbl.get_height() // 2)))
        
    elif game_state["intro_stage"] == "SPIEL":
        welcome_lbl = FONT_SUBTITLE.render(f"Welcome aboard, {game_state['character_name']}!", True, GREEN_BUTTON)
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
        screen.blit(start_lbl, (btn_start.x + (btn_start.width // 2 - start_lbl.get_width() // 2), btn_start.y + (btn_start.height // 2 - start_lbl.get_height() // 2)))

def draw_game_screen():
    screen.fill(BG_COLOR)
    
    # --- HEADER MANAGEMENT PANEL ---
    header_rect = pygame.Rect(20, 15, 1160, 70)
    pygame.draw.rect(screen, PANEL_COLOR, header_rect, border_radius=10)
    pygame.draw.rect(screen, ACCENT_COLOR, header_rect, width=2, border_radius=10)
    
    chef_surf = FONT_SUBTITLE.render(f"🧑‍🍳 Chef: {game_state['character_name']}", True, TEXT_COLOR)
    screen.blit(chef_surf, (40, 35))
    
    money_surf = FONT_SUBTITLE.render(f"💰 Earnings: ${game_state['money']:.2f}", True, GREEN_BUTTON)
    screen.blit(money_surf, (300, 35))
    
    elapsed = time.time() - game_state["start_time"]
    time_str = f"🕒 Time: {int(elapsed // 60):02d}:{int(elapsed % 60):02d}"
    time_surf = FONT_SUBTITLE.render(time_str, True, TEXT_COLOR)
    screen.blit(time_surf, (WIDTH - time_surf.get_width() - 40, 35))
    
    # --- LIVE ORDER TICKET RAIL ---
    rail_rect = pygame.Rect(20, 100, 1160, 160)
    pygame.draw.rect(screen, PANEL_COLOR, rail_rect, border_radius=10)
    pygame.draw.rect(screen, BORDER_COLOR, rail_rect, width=1, border_radius=10)
    
    rail_lbl = FONT_BODY.render("🎟️ ACTIVE ORDER TICKETS (TAKEN ORDERS)", True, BORDER_COLOR)
    screen.blit(rail_lbl, (35, 105))
    
    if not game_state["tickets"]:
        empty_lbl = FONT_SUBTITLE.render("[ No active tickets. Head to Front Counter to take customer orders! ]", True, BORDER_COLOR)
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
        screen.blit(lbl, (btn.x + (btn.width // 2 - lbl.get_width() // 2), btn.y + (btn.height // 2 - lbl.get_height() // 2)))

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
                
                info_txt = f"👤 {cust['name']} - Waiting to Order"
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
            lbl = FONT_SUBTITLE.render("📝 TAKE ORDER SLIP", True, PANEL_COLOR)
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
            lbl = FONT_SUBTITLE.render(f"➕ Pipe {shp}", True, PANEL_COLOR)
            screen.blit(lbl, (btn_pipe.x + (btn_pipe.width // 2 - lbl.get_width() // 2), btn_pipe.y + (btn_pipe.height // 2 - lbl.get_height() // 2)))
            
        tray_box = pygame.Rect(290, 480, 860, 270)
        pygame.draw.rect(screen, BG_COLOR, tray_box, border_radius=8)
        pygame.draw.rect(screen, BORDER_COLOR, tray_box, width=1, border_radius=8)
        screen.blit(FONT_SUBTITLE.render("Prepared Tray Queue (Ready to Fry):", True, TEXT_COLOR), (310, 495))
        
        if not game_state["prepared_dough_queue"]:
            screen.blit(FONT_BODY.render("Tray is empty. Pipe dough shapes above to fill it.", True, BORDER_COLOR), (310, 540))
        else:
            for d_idx, shp in enumerate(game_state["prepared_dough_queue"][:14]):
                gx = 310 + (d_idx % 5 * 165)
                gy = 540 + (d_idx // 5 * 65)
                box = pygame.Rect(gx, gy, 150, 50)
                pygame.draw.rect(screen, PANEL_COLOR, box, border_radius=4)
                pygame.draw.rect(screen, BORDER_COLOR, box, 1, border_radius=4)
                screen.blit(FONT_BODY.render(f"🥟 {shp}", True, TEXT_COLOR), (gx + 15, gy + 15))

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
            
            # Independent Slot Render Blocks
            s1_rect = pygame.Rect(fx + 15, fy + 40, 380, 60)
            s2_rect = pygame.Rect(fx + 15, fy + 110, 380, 60)
            slots = [(s1_rect, 0), (s2_rect, 1)]
            
            for s_rect, idx in slots:
                if idx < len(items):
                    churro = items[idx]
                    if churro["status"] == "Frying Side 1":
                        pygame.draw.rect(screen, PANEL_COLOR, s_rect, border_radius=6)
                        pygame.draw.rect(screen, BORDER_COLOR, s_rect, width=1, border_radius=6)
                        lbl_txt = f"⏳ {churro['shape']}: Side 1 ({max(0.0, churro['time_left']):.1f}s)"
                        lbl_color = TEXT_COLOR
                    elif churro["status"] == "Ready to Flip":
                        pygame.draw.rect(screen, ACCENT_COLOR, s_rect, border_radius=6)
                        lbl_txt = f"🔄 FLIP {churro['shape'].upper()}"
                        lbl_color = PANEL_COLOR
                    elif churro["status"] == "Frying Side 2":
                        pygame.draw.rect(screen, PANEL_COLOR, s_rect, border_radius=6)
                        pygame.draw.rect(screen, BORDER_COLOR, s_rect, width=1, border_radius=6)
                        lbl_txt = f"⏳ {churro['shape']}: Side 2 ({max(0.0, churro['time_left']):.1f}s)"
                        lbl_color = TEXT_COLOR
                    elif churro["status"] == "Ready to Collect":
                        pygame.draw.rect(screen, GREEN_BUTTON, s_rect, border_radius=6)
                        lbl_txt = f"📥 COLLECT {churro['shape'].upper()}"
                        lbl_color = PANEL_COLOR
                    
                    surf = FONT_BODY.render(lbl_txt, True, lbl_color)
                    screen.blit(surf, (s_rect.x + 15, s_rect.y + (s_rect.height // 2 - surf.get_height() // 2)))
                else:
                    # Slot is empty
                    if idx == len(items) and game_state["prepared_dough_queue"]:
                        pygame.draw.rect(screen, BLUE_BUTTON, s_rect, border_radius=6)
                        lbl_txt = f"➕ Drop {game_state['prepared_dough_queue'][0]}"
                        lbl_color = PANEL_COLOR
                    else:
                        pygame.draw.rect(screen, PANEL_COLOR, s_rect, border_radius=6)
                        # FIXED: Removed the invalid border_style=1 argument
                        pygame.draw.rect(screen, BORDER_COLOR, s_rect, width=1, border_radius=6)
                        lbl_txt = "[ Empty Slot ]"
                        lbl_color = BORDER_COLOR
                        
                    surf = FONT_BODY.render(lbl_txt, True, lbl_color)
                    screen.blit(surf, (s_rect.x + (s_rect.width // 2 - surf.get_width() // 2), s_rect.y + (s_rect.height // 2 - surf.get_height() // 2)))

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
                workbench_lines.append(f"  • {qty}x {shape_name}")
        else:
            workbench_lines.append("  • (Plate is empty)")
            
        ly = 365
        for line in workbench_lines:
            screen.blit(FONT_BODY.render(line, True, TEXT_COLOR), (870, ly))
            ly += 26
            
        btn_build = pygame.Rect(870, 560, 270, 55)
        has_items = len(game_state["active_plate"]["churros"]) > 0
        is_locked = game_state["active_plate"]["is_locked"]
        
        btn_color = BORDER_COLOR if not has_items else (ACCENT_COLOR if is_locked else GREEN_BUTTON)
        pygame.draw.rect(screen, btn_color, btn_build, border_radius=8)
        
        status_lbl = "Locked & Ready" if is_locked else "✨ Coat & Lock Plate"
        lbl_b = FONT_SUBTITLE.render(status_lbl, True, PANEL_COLOR)
        screen.blit(lbl_b, (btn_build.x + (btn_build.width // 2 - lbl_b.get_width() // 2), btn_build.y + 16))
        
        # Bottom Inventory Display Box (Fried Bin)
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
                screen.blit(FONT_BODY.render(f"🥟 {plate['shape']}", True, TEXT_COLOR), (p_rect.x + 15, p_rect.y + 14))

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
            
            q_verif = f"Quantity: {len(churros_on_plate)} / {active_ticket['qty']} " + ("✅" if match_qty else "❌")
            sh_verif = f"Shape Type Match: " + ("✅" if match_shape else "❌")
            s_verif = f"Sauce Coating: {plate['sauce']} " + ("✅" if match_sauce else f"❌ (Expected {active_ticket['sauce']})")
            t_verif = f"Topping Shaker: {plate['topping']} " + ("✅" if match_top else f"❌ (Expected {active_ticket['topping']})")
            
            screen.blit(FONT_BODY.render(q_verif, True, GREEN_BUTTON if match_qty else RED_BUTTON), (320, 460))
            screen.blit(FONT_BODY.render(sh_verif, True, GREEN_BUTTON if match_shape else RED_BUTTON), (320, 488))
            screen.blit(FONT_BODY.render(s_verif, True, GREEN_BUTTON if match_sauce else RED_BUTTON), (320, 516))
            screen.blit(FONT_BODY.render(t_verif, True, GREEN_BUTTON if match_top else RED_BUTTON), (320, 544))
            
            btn_pay = pygame.Rect(290, 640, 860, 70)
            pygame.draw.rect(screen, GREEN_BUTTON if plate["is_locked"] else BORDER_COLOR, btn_pay, border_radius=10)
            lbl_p = FONT_TITLE.render("💰 SERVE PLATE & COLLECT PAYMENT", True, PANEL_COLOR)
            screen.blit(lbl_p, (btn_pay.x + (btn_pay.width // 2 - lbl_p.get_width() // 2), btn_pay.y + 15))

# --- INTERACTIVE CLICK REACTION HANDLER HUB ---
def handle_gameplay_clicks(mx, my):
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
                    "topping": random.choice(toppings)
                }
                game_state["tickets"].append(new_ticket)
            
    elif current == "Pastry Station":
        shapes = ["Straight", "Loop", "Spiral"]
        for idx, shp in enumerate(shapes):
            btn_pipe = pygame.Rect(290 + (idx * 290), 360, 260, 80)
            if btn_pipe.collidepoint((mx, my)):
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
            
            # Slot 1 Interactions
            if s1_rect.collidepoint((mx, my)):
                if len(items) >= 1:
                    churro = items[0]
                    if churro["status"] == "Ready to Flip":
                        churro["status"] = "Frying Side 2"
                        churro["time_left"] = 8.0
                    elif churro["status"] == "Ready to Collect":
                        game_state["finished_plates"].append({"shape": churro["shape"]})
                        items.pop(0)
                elif len(items) == 0 and game_state["prepared_dough_queue"]:
                    next_dough = game_state["prepared_dough_queue"].pop(0)
                    items.append({"status": "Frying Side 1", "shape": next_dough, "time_left": 10.0})
                return
                
            # Slot 2 Interactions
            if s2_rect.collidepoint((mx, my)):
                if len(items) == 2:
                    churro = items[1]
                    if churro["status"] == "Ready to Flip":
                        churro["status"] = "Frying Side 2"
                        churro["time_left"] = 8.0
                    elif churro["status"] == "Ready to Collect":
                        game_state["finished_plates"].append({"shape": churro["shape"]})
                        items.pop(1)
                elif len(items) == 1 and game_state["prepared_dough_queue"]:
                    next_dough = game_state["prepared_dough_queue"].pop(0)
                    items.append({"status": "Frying Side 1", "shape": next_dough, "time_left": 10.0})
                return

    elif current == "Topping Station":
        # Sauce buttons interaction loop
        sauces = ["None", "Chocolate", "Caramel", "Condensed Milk"]
        for idx, s in enumerate(sauces):
            btn_s = pygame.Rect(290, 350 + (idx * 55), 240, 48)
            if btn_s.collidepoint((mx, my)):
                game_state["active_plate"]["sauce"] = s
                return
                
        # Toppings buttons interaction loop
        toppings = ["None", "Cinnamon Sugar", "Sprinkles", "Crushed Oreos"]
        for idx, t in enumerate(toppings):
            btn_t = pygame.Rect(570, 350 + (idx * 55), 240, 48)
            if btn_t.collidepoint((mx, my)):
                game_state["active_plate"]["topping"] = t
                return
                
        # Lock Action button
        btn_build = pygame.Rect(870, 560, 270, 55)
        if btn_build.collidepoint((mx, my)) and game_state["active_plate"]["churros"]:
            game_state["active_plate"]["is_locked"] = True
            return
            
        # Add multiple pieces to the plate from the bin row
        for p_idx, plate in enumerate(game_state["finished_plates"][:6]):
            p_rect = pygame.Rect(310 + (p_idx * 140), 700, 120, 45)
            if p_rect.collidepoint((mx, my)):
                moved_item = game_state["finished_plates"].pop(p_idx)
                game_state["active_plate"]["churros"].append(moved_item["shape"])
                return

    elif current == "Pay Counter" and game_state["tickets"]:
        btn_pay = pygame.Rect(290, 640, 860, 70)
        if btn_pay.collidepoint((mx, my)) and game_state["active_plate"]["is_locked"]:
            active_ticket = game_state["tickets"].pop(0)
            plate = game_state["active_plate"]
                
            match_qty = (len(plate["churros"]) == active_ticket["qty"])
            match_shape = all(s == active_ticket["shape"] for s in plate["churros"]) if plate["churros"] else False
            match_sauce = (plate["sauce"] == active_ticket["sauce"])
            match_top = (plate["topping"] == active_ticket["topping"])
            
            payout = active_ticket["qty"] * 2.50
            if match_qty and match_shape and match_sauce and match_top:
                payout += 5.00  
            elif not match_sauce or not match_top or not match_qty:
                payout = max(1.00, payout - 4.00) 
                
            game_state["money"] += payout
            
            game_state["active_plate"] = {
                "churros": [],
                "sauce": "None",
                "topping": "None",
                "is_locked": False
            }

# --- SYSTEM MAIN RUNTIME LOOP ---
while game_state["is_running"]:
    if game_state["screen_state"] == "INTRO":
        draw_intro_screen()
    else:
        handle_automatic_arrivals() 
        update_fryer_timers()      
        draw_game_screen()
        
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_state["is_running"] = False
            
        elif event.type == pygame.KEYDOWN:
            if game_state["screen_state"] == "INTRO" and game_state["intro_stage"] == "NAME":
                if event.key == pygame.K_RETURN:
                    if len(input_name_buffer.strip()) > 0:
                        game_state["character_name"] = input_name_buffer.strip()
                        game_state["intro_stage"] = "SPIEL"
                elif event.key == pygame.K_BACKSPACE:
                    input_name_buffer = input_name_buffer[:-1]
                else:
                    if len(input_name_buffer) < 16 and event.unicode.isprintable():
                        input_name_buffer += event.unicode
                        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            
            if game_state["screen_state"] == "INTRO":
                if game_state["intro_stage"] == "NAME":
                    btn_continue = pygame.Rect(500, 520, 200, 50)
                    if btn_continue.collidepoint((mx, my)) and len(input_name_buffer.strip()) > 0:
                        game_state["character_name"] = input_name_buffer.strip()
                        game_state["intro_stage"] = "SPIEL"
                elif game_state["intro_stage"] == "SPIEL":
                    btn_start = pygame.Rect(450, 580, 300, 60)
                    if btn_start.collidepoint((mx, my)):
                        game_state["screen_state"] = "GAME"
                        game_state["start_time"] = time.time()
                        game_state["last_arrival_time"] = time.time()
                        game_state["waiting_customers"].append({"name": "Papa Louie"})
                        game_state["waiting_customers"].append({"name": "Wally"})
            else:
                handle_gameplay_clicks(mx, my)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()