import tkinter as tk
from PIL import Image, ImageTk
import random
import pygame
import math
import sys

class Pet:
    """
    A class to create a transparent, always-on-top desktop pet application.
    Each instance of this class is a separate pet.
    """
    def __init__(self, master, gif_path, dialogue_sound, start_x, start_y):
        self.master = master
        master.title("Desktop Pet")
        
        self.frames = []
        self.delays = [] 
        self.current_frame = 0
        self.animation_timer = None 

        self.current_gif_path = ""
        
        self._load_gif_frames(gif_path, (121, 200))

        # --- Window Configuration ---
        master.overrideredirect(True)
        master.attributes('-transparentcolor', '#000000')
        master.attributes('-topmost', True)
        
        self.width = self.frames[0].width()
        self.height = self.frames[0].height()
        master.geometry(f'{self.width}x{self.height}+{start_x}+{start_y}')

        self.label = tk.Label(master, image=self.frames[0], bg='#000000')
        self.label.pack()

        # --- Mouse Event Handling for Drag and Drop ---
        self.label.bind("<Button-1>", self.start_move)
        self.label.bind("<Button-3>", self.show_menu)
        self.label.bind("<B1-Motion>", self.move_window)

        # --- Animation Loop ---
        self.animate()

        # --- Dialogue Bubble Setup ---
        self.dialogues = [
            "HELLO FROM MR ANTENNA!",
            "Wow, what an AMAZING performance!",
            "MIKE, PLAY THE VHS!!!",
            "Coming straight from YOUR house!",
            "What LOVELY contestants we've got TODAY, folks---!!!",
            "He's groovy and NEVER glooby!",
            "TV Time.png",
            "We'll be right back after these messages! ...I'm talking about your work messages, by the way!",
            "And now, a word from our sponsor... which is ME! Mr. Antenna!",
            "Is this thing on? Hello? Just checking. Don't mind me folks!",
        ]

        try:
            image_obj = Image.open("TV Time.png")
            resized_image = image_obj.resize((420, 420))
            self.tv_time_image = ImageTk.PhotoImage(resized_image)
        except FileNotFoundError:
            print("Error: 'TV Time.png' not found. Please ensure the image is in the same directory.")
            self.tv_time_image = None 
        
        # --- Opaque Window for Text Dialogue ---
        self.text_bubble_window = tk.Toplevel(self.master)
        self.text_bubble_window.overrideredirect(True)
        self.text_bubble_window.attributes('-topmost', True)
        self.text_bubble_window.config(bg='black') 
        self.text_bubble_window.withdraw() 

        self.dialogue_label = tk.Label(
            self.text_bubble_window,
            text="",
            font=("Pixel Operator", 10),
            bg="black",
            fg="white",
            padx=10,
            pady=5,
            wraplength=150
        )
        self.dialogue_label.pack()

        # --- Transparent Window for Image Dialogue ---
        self.image_bubble_window = tk.Toplevel(self.master)
        self.image_bubble_window.overrideredirect(True)
        self.image_bubble_window.attributes('-topmost', True)
        self.image_bubble_window.attributes('-transparentcolor', 'black') 
        self.image_bubble_window.config(bg='black') 
        self.image_bubble_window.withdraw() 

        self.image_label = tk.Label(
            self.image_bubble_window,
            image=None,
            bg='black'
        )
        self.image_label.pack()

        # --- Audio Setup ---
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(dialogue_sound)
        self.sound_enabled = True
        
        self.is_moving = False
        self.movement_timer = None 
        
        self.dest_x = 0
        self.dest_y = 0
        self.step_x = 0
        self.step_y = 0
        self.master.after(100, self.update_position)

        self.dialogue_timer = self.master.after(15000, self.show_dialogue)
    
    def _load_gif_frames(self, gif_path, size=None):
        """Loads a GIF, resizes it, and populates the frames and delays list."""
        self.image = Image.open(gif_path)
        self.current_gif_path = gif_path

        if size is None:
            resize_size = (121, 200) 
        else:
            resize_size = size
        
        self.frames = []
        self.delays = [] 
        self.current_frame = 0
        
        try:
            while True:
                frame = self.image.copy()
                
                # Check for transparency and apply it
                if 'transparency' in self.image.info:
                    transparent_color = self.image.info['transparency']
                    # Convert the frame to RGBA to handle transparency correctly
                    frame = frame.convert('RGBA')
                    
                    # Create a new image with the transparent background
                    # This is more robust than modifying the palette directly
                    new_frame_data = []
                    for item in frame.getdata():
                        # The transparent color needs to be handled differently based on the image mode
                        if frame.mode == 'P':
                            if item == transparent_color:
                                new_frame_data.append((0, 0, 0, 0))  # Set alpha to 0 for transparency
                            else:
                                new_frame_data.append(item)
                        elif frame.mode == 'RGB':
                            if item[:3] == transparent_color:
                                new_frame_data.append((item[0], item[1], item[2], 0))
                            else:
                                new_frame_data.append(item)
                        else:
                            new_frame_data.append(item)
                    
                    frame.putdata(new_frame_data)
                    
                resized_frame = frame.resize(resize_size, Image.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(resized_frame))
                self.delays.append(self.image.info['duration']) 
                self.image.seek(len(self.frames))
        except EOFError:
            pass
            
    def move_to_new_destination(self):
        """This method picks a new, random destination for the pet."""
        current_x = self.master.winfo_x()
        current_y = self.master.winfo_y()

        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        
        min_x = int(screen_width * 0.25)
        max_x = int(screen_width * 0.75)
        min_y = int(screen_height * 0.25)
        max_y = int(screen_height * 0.75)

        self.dest_x = random.randint(min_x, max_x)
        self.dest_y = random.randint(min_y, max_y)

        dx = self.dest_x - current_x
        dy = self.dest_y - current_y
        
        speed = 2
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.step_x = (dx / distance) * speed
            self.step_y = (dy / distance) * speed
        else:
            self.step_x = 0
            self.step_y = 0

        if self.is_moving:
            self.movement_timer = self.master.after(random.randint(1000, 5000), self.move_to_new_destination)
    
    def update_position(self):
        """This method moves the pet one step closer to its destination."""
        
        if self.is_moving:
            current_x = self.master.winfo_x()
            current_y = self.master.winfo_y()
            new_x = current_x + self.step_x
            new_y = current_y + self.step_y

            hit_boundary = False
            if new_x <= 0:
                new_x = 0
                self.step_x = -self.step_x
                hit_boundary = True
            if new_x >= self.master.winfo_screenwidth() - self.width:
                new_x = self.master.winfo_screenwidth() - self.width
                self.step_x = -self.step_x
                hit_boundary = True
            if new_y <= 0:
                new_y = 0
                self.step_y = -self.step_y
                hit_boundary = True
            if new_y >= self.master.winfo_screenheight() - self.height:
                new_y = self.master.winfo_screenheight() - self.height
                self.step_y = -self.step_y
                hit_boundary = True
            if hit_boundary:
                self.move_to_new_destination()

            self.master.geometry(f'{self.width}x{self.height}+{int(new_x)}+{int(new_y)}')

        current_x = self.master.winfo_x()
        current_y = self.master.winfo_y()
        self.text_bubble_window.geometry(f'+{int(current_x + 50)}+{int(current_y - 30)}')
        self.image_bubble_window.geometry(f'+{int(current_x + 50)}+{int(current_y - 30)}')

        self.master.after(10, self.update_position)

    def start_moving(self):
        """Starts the pet's random movement."""
        if not self.is_moving:
            self.is_moving = True
            self.move_to_new_destination()

    def stop_moving(self):
        """Stops the pet's movement."""
        self.is_moving = False
        if self.movement_timer:
            self.master.after_cancel(self.movement_timer)
            self.movement_timer = None
    
    def change_gif(self, new_gif_path, size=None):
        """Loads a new GIF and updates the pet's animation."""
        if self.animation_timer:
            self.master.after_cancel(self.animation_timer)

        self._load_gif_frames(new_gif_path, size) 

        self.width = self.frames[0].width()
        self.height = self.frames[0].height()
        current_x = self.master.winfo_x()
        current_y = self.master.winfo_y()
        self.master.geometry(f'{self.width}x{self.height}+{current_x}+{current_y}')

        self.animate()
    
    def toggle_sound(self):
        ''' Toggles the sound_enabled flag. '''
        self.sound_enabled = not self.sound_enabled
    
    def compliment_pet(self):
        """Changes the GIF and displays a compliment-related dialogue simultaneously, then reverts the GIF."""
        compliment_dialogues = [
            "OHHH, YOU'RE TOO KIND!",
            "I'M SO GLAD YOU THINK SO!"
        ]
        dialogue = random.choice(compliment_dialogues)

        self.change_gif("deltarune-bowing.gif", (121, 200))
        
        self.show_dialogue(dialogue)
        
        self.master.after(4500, lambda: self.change_gif("deltarune-tenna.gif", (121, 200)))

    def show_gif_options(self, menu):
        """Populates the GIF submenu."""
        menu.add_command(label="Random Tenna", command=self.random_gif)
        menu.add_command(label="Default", command=lambda: self.change_gif("deltarune-tenna.gif", (121, 200)))
        menu.add_command(label="Dancing", command=lambda: self.change_gif("tenna-dancing-two.gif", (121, 200)))
        menu.add_command(label="T-Posing", command=lambda: self.change_gif("deltarune-tpose.gif", (121, 200)))
        menu.add_command(label="Violent", command=lambda: self.change_gif("deltarune-kick.gif", (121, 200)))
        menu.add_command(label="Bowing", command=lambda: self.change_gif("deltarune-bowing.gif", (121, 200)))
        menu.add_command(label="GANGMAN STYLE", command=lambda: self.change_gif("deltarune-GANGNAMSTYLE.gif", (121, 200)))
        menu.add_command(label="Macarena", command=lambda: self.change_gif("deltarune-macarena.gif", (121, 200)))

    def random_gif(self):
        """Selects a random GIF from the available options."""
        gif_options = [
            ("deltarune-tenna.gif", (121, 200)),
            ("tenna-dancing-two.gif", (121, 200)),
            ("deltarune-tpose.gif", (121, 200)),
            ("deltarune-kick.gif", (121, 200)),
            ("deltarune-bowing.gif", (121, 200)),
            ("deltarune-GANGNAMSTYLE.gif", (121, 200)),
            ("deltarune-macarena.gif", (121, 200))
        ]
        selected_gif = random.choice(gif_options)
        self.change_gif(selected_gif[0], selected_gif[1])

    def show_menu(self, event):
        ''' Displays a context menu on right-click. '''
        menu = tk.Menu(self.master, tearoff=0)
        
        menu.add_command(label="Compliment Tenna", command=self.compliment_pet)
        menu.add_command(
            label="Pat Tenna",
            command=lambda: (
                self.show_dialogue("HEY! NO PATTING MR ANTENNA"),
                self.change_gif("deltarune-pat.gif", (121, 200)),
                self.master.after(4500, lambda: self.change_gif("deltarune-tenna.gif", (121, 200)))
            )
        )
        
        # --- NEW SUBMENU FOR GIFS ---
        gif_menu = tk.Menu(menu, tearoff=0)
        self.show_gif_options(gif_menu)
        menu.add_cascade(label="Change GIF", menu=gif_menu)
        
        def exit_with_explosion():
            self.change_gif("deltarune-explosion.gif", (121, 200))
            self.sound = pygame.mixer.Sound("deltarune-explosion.mp3")
            if self.sound_enabled:
                self.sound.play()
            self.master.after(2000, lambda: self.master.destroy())

        menu.add_command(label="Exit", command=exit_with_explosion)
        menu.add_command(label="Say hello!", command=lambda: self.show_dialogue("HELLO FROM MR ANTENNA!"))
        
        if self.is_moving:
            menu.add_command(label="Turn off random Tenna", command=self.stop_moving)
        else:
            menu.add_command(label="Turn on random Tenna", command=self.start_moving)
        
        menu.add_command(label="Make Pet Bigger", command=lambda: self.change_gif(self.current_gif_path, (180, 300)))
        menu.add_command(label="Make Pet Smaller", command=lambda: self.change_gif(self.current_gif_path, (90, 150)))
        menu.add_command(label="Reset Size", command=lambda: self.change_gif(self.current_gif_path, (121, 200)))

        if self.sound_enabled:
            menu.add_command(label="Disable Sound", command=self.toggle_sound)
        else:
            menu.add_command(label="Enable Sound", command=self.toggle_sound)
        
        menu.post(event.x_root, event.y_root)

    def start_move(self, event):
        """Records the starting position of the mouse for dragging."""
        self.x = event.x
        self.y = event.y

    def move_window(self, event):
        """Moves the window as the mouse is dragged."""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry(f'+{x}+{y}')
        self.text_bubble_window.geometry(f'+{x + 50}+{y - 30}')
        self.image_bubble_window.geometry(f'+{x + 50}+{y - 30}')

    def animate(self):
        """Updates the GIF frame to create animation."""
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.label.config(image=self.frames[self.current_frame])
        
        delay = self.delays[self.current_frame]
        if delay < 20: 
            delay = 20

        self.animation_timer = self.master.after(delay, self.animate)

    def show_dialogue(self, dialogue=None):
        """Displays a dialogue line in the text bubble and plays a sound."""
        if self.dialogue_timer:
            self.master.after_cancel(self.dialogue_timer)
        
        if dialogue is None:
            random_dialogues = self.dialogues.copy()
            try:
                random_dialogues.remove("HELLO FROM MR ANTENNA!")
            except ValueError:
                pass
            dialogue = random.choice(random_dialogues)
        else:
            pass
            
        self.text_bubble_window.withdraw()
        self.image_bubble_window.withdraw()

        if dialogue == "TV Time.png" and self.tv_time_image:
            self.image_label.config(image=self.tv_time_image)
            self.image_bubble_window.geometry(f'+{self.master.winfo_x() + 50}+{self.master.winfo_y() - 30}')
            self.image_bubble_window.deiconify()
        else:
            self.dialogue_label.config(text=dialogue, image="")
            self.text_bubble_window.geometry(f'+{self.master.winfo_x() + 50}+{self.master.winfo_y() - 30}')
            self.text_bubble_window.deiconify()
        
        if self.sound_enabled:
            self.sound.play()
        
        self.master.after(4500, self.hide_dialogue)
        self.dialogue_timer = self.master.after(45000, self.show_dialogue)

    def hide_dialogue(self):
        """Hides both dialogue windows."""
        self.text_bubble_window.withdraw()
        self.image_bubble_window.withdraw()

# --- SpamtonPet Class (with custom logic) ---
class SpamtonPet(Pet):
    def __init__(self, master, start_x, start_y):
        super().__init__(master, "spamton-deltarune.gif", "spamton-talking.mp3", start_x, start_y)
        
        self.dialogues = [
            "[[BIG SHOT]]!",
            "Wanna be a [[BIG SHOT]]?",
            "[[NUMBER ONE RATED SALESMAN 1997]]!",
            "I'm gonna be a [[BIG SHOT]]! A [[BIG SHOT]]!"
        ]
    
    def compliment_spamton(self):
        compliment_dialogues = [
            "HAEHAEHAEHAE! DON'T GET MY [[HEART SHAPED OBJECT]] ALL BENT OUT OF SHAPE!",
            "[[THANKS]] FOR THE [[KROMER]], KID!"
        ]
        dialogue = random.choice(compliment_dialogues)
        self.change_gif("spamton-happy.gif", (121, 200))
        self.show_dialogue(dialogue)
        self.master.after(4500, lambda: self.change_gif("spamton-deltarune.gif", (121, 200)))
        
    def pat_spamton(self):
        self.show_dialogue("[[STOP]]! THIS IS NOT A [[DEAL]]!")
        self.change_gif("spamton-blush.gif", (121, 200))
        self.master.after(4500, lambda: self.change_gif("spamton-deltarune.gif", (121, 200)))
    
    def show_gif_options(self, menu):
        menu.add_command(label="Random Spamton", command=self.random_gif)
        menu.add_command(label="Default", command=lambda: self.change_gif("spamton-deltarune.gif", (121, 200)))
        menu.add_command(label="Spinning", command=lambda: self.change_gif("spamton-spinning.gif", (121, 200)))
        menu.add_command(label="Happy", command=lambda: self.change_gif("spamton-happy.gif", (121, 200)))
        menu.add_command(label="Mad", command=lambda: self.change_gif("spamton-mad.gif", (121, 200)))
        menu.add_command(label="Death..", command=lambda: self.change_gif("spamton-dead.gif", (121, 200)))

    def show_menu(self, event):
        menu = tk.Menu(self.master, tearoff=0)
        
        menu.add_command(label="Compliment Spamton", command=self.compliment_spamton)
        menu.add_command(label="Pat Spamton", command=self.pat_spamton)
        
        gif_menu = tk.Menu(menu, tearoff=0)
        self.show_gif_options(gif_menu)
        menu.add_cascade(label="Change GIF", menu=gif_menu)
        
        def exit_spamton_with_explosion():
            self.change_gif("spamton-explosion.gif", (121, 200))
            self.sound = pygame.mixer.Sound("deltarune-explosion.mp3")
            if self.sound_enabled:
                self.sound.play()
            self.master.after(2000, lambda: self.master.destroy())
            
        menu.add_command(label="Exit", command=exit_spamton_with_explosion)
        menu.add_command(label="Say hello!", command=lambda: self.show_dialogue("H3LLO!!! YOU [[LITTLE SPONGE]]"))
        
        if self.is_moving:
            menu.add_command(label="Turn off random Spamton", command=self.stop_moving)
        else:
            menu.add_command(label="Turn on random Spamton", command=self.start_moving)
            
        menu.add_command(label="Make Pet Bigger", command=lambda: self.change_gif(self.current_gif_path, (180, 300)))
        menu.add_command(label="Make Pet Smaller", command=lambda: self.change_gif(self.current_gif_path, (90, 150)))
        menu.add_command(label="Reset Size", command=lambda: self.change_gif(self.current_gif_path, (121, 200)))
        
        if self.sound_enabled:
            menu.add_command(label="Disable Sound", command=self.toggle_sound)
        else:
            menu.add_command(label="Enable Sound", command=self.toggle_sound)
        
        menu.post(event.x_root, event.y_root)

    def random_gif(self):
        gif_options = [
            ("spamton-deltarune.gif", (121, 200)),
            ("spamton-spinning.gif", (121, 200)),
            ("spamton-happy.gif", (121, 200)),
            ("spamton-mad.gif", (121, 200)),
            ("spamton-flying.gif", (121, 200))
        ]
        selected_gif = random.choice(gif_options)
        self.change_gif(selected_gif[0], selected_gif[1])


# --- SecretPet Class (New) ---
class SecretPet(Pet):
    def __init__(self, master, start_x, start_y):
        super().__init__(master, "deltarune-toby-dog.gif", "toby-dog-sound.mp3", start_x, start_y)
        
        self.dialogues = [
            "WOOF! You found me!",
            "bark bark bark",
            "how tf did yo ahh find my dog ahh vro get tf out vro",
            "AUDIO:dogsong.mp3"
        ]

    def show_dialogue(self, dialogue=None):
        """
        Displays a dialogue line in the text bubble and plays a sound.
        """
        if self.dialogue_timer:
            self.master.after_cancel(self.dialogue_timer)

        if dialogue is None:
            random_dialogues = self.dialogues.copy()
            dialogue = random.choice(random_dialogues)
        # Check if the dialogue is an audio file trigger
        if isinstance(dialogue, str) and dialogue.startswith("AUDIO:"):
            audio_file = dialogue.split("AUDIO:")[1].strip()
            if self.sound_enabled:
                sound = pygame.mixer.Sound(audio_file)
                sound.play()
            self.master.after(4500, self.hide_dialogue)
            self.dialogue_timer = self.master.after(45000, self.show_dialogue)
            return

        self.text_bubble_window.withdraw()
        self.image_bubble_window.withdraw()

        self.dialogue_label.config(text=dialogue, image="")
        self.text_bubble_window.geometry(f'+{self.master.winfo_x() + 50}+{self.master.winfo_y() - 30}')
        self.text_bubble_window.deiconify()

        if self.sound_enabled:
            self.sound.play()

        self.master.after(4500, self.hide_dialogue)
        self.dialogue_timer = self.master.after(45000, self.show_dialogue)
    
    def show_menu(self, event):
        menu = tk.Menu(self.master, tearoff=0)
        
        menu.add_command(label="Pat Dog", command=lambda: self.show_dialogue("WOOF!"))
        menu.add_command(label="...", command=lambda: (self.change_gif("toby-fox-mlg.gif", (121, 200)), self.show_dialogue("WASSUPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP")))
        menu.add_command(label="hapi toby or something", command=lambda: self.change_gif("tobyfoxhappy.gif", (1000, 1500)))
        def spinny_car_animation(times=50):
            if times > 0:
                self.change_gif("spinny car.gif", (200, 300))
                self.master.after(20, lambda: spinny_car_animation(times - 1))
        menu.add_command(label="good luck.", command=lambda: spinny_car_animation())
        menu.add_command(label="this is completely unrelated to this dog", command=lambda: self.change_gif("deltarune-havingamoment.gif", (121, 200)))
        menu.add_command(label="Make Dog Bigger", command=lambda: self.change_gif("tobynyan.gif", (500, 750)))
        menu.add_command(label="Make Dog Smaller", command=lambda: self.change_gif(self.current_gif_path, (800, 100)))
        menu.add_command(label="Reset Size", command=lambda: (self.change_gif(self.current_gif_path, (500, 600)), self.show_dialogue("yeah you can't change this.")))
        
        
        gif_menu = tk.Menu(menu, tearoff=0)
        gif_menu.add_command(label="Default", command=lambda: self.change_gif("deltarune-toby-dog.gif", (121, 200)))
        gif_menu.add_command(label="Happy Dog", command=lambda: self.change_gif("toby-dog-happy.gif", (1000, 1500)))
        menu.add_cascade(label="Change GIF", menu=gif_menu)
        def disable_sound():
            self.sound.set_volume(10000)
        menu.add_command(label="disable sound", command=disable_sound)
        menu.add_command(
            label="Make Doggo Sad",
            command=lambda: (
                self.change_gif("toby-dog-sad.gif", (121, 200)),
                self.master.after(2000, lambda: self.change_gif("deltarune-toby-dog.gif", (121, 200))),
                self.master.after(2000, lambda: self.master.destroy())
            )
        )
        menu.add_command(label="Exit", command=lambda: self.master.destroy())
        
        menu.post(event.x_root, event.y_root)

# --- PetManager Class (Re-implemented) ---
class PetManager:
    """Manages the creation of multiple pet instances."""
    def __init__(self, master):
        self.master = master
        master.title("Pet Launcher")
        master.geometry('200x175')
        
        self.pets = []
        self.secret_click_count = 0
        self.secret_button_unlocked = False

        label = tk.Label(master, text="Close this window when done!")
        label.pack(pady=10)
        
        btn_tenna = tk.Button(master, text="Launch Tenna", command=self.create_tenna)
        btn_tenna.pack(pady=5)
        
        btn_spamton = tk.Button(master, text="Launch Spamton", command=self.create_spamton)
        btn_spamton.pack(pady=5)
        
        # Bind the entire window to detect clicks for the secret button
        master.bind("<Button-1>", self.check_secret_clicks)

        # The secret button is hidden until unlocked
        self.btn_secret = tk.Button(master, text="Launch Secret Pet!", command=self.create_secret_pet)
        self.btn_secret.pack_forget()

    def check_secret_clicks(self, event):
        """Increments a counter and reveals the secret button if a threshold is met."""
        self.secret_click_count += 1
        print(f"{self.secret_click_count}")
        if self.secret_click_count >= 5 and not self.secret_button_unlocked:  # The "secret" is 5 clicks on the launcher window
            self.reveal_secret_button()
            self.secret_button_unlocked = True

    def reveal_secret_button(self):
        """Shows the hidden secret button."""
        self.btn_secret.pack(pady=5)

    def create_tenna(self):
        new_pet_window = tk.Toplevel(self.master)
        new_pet = Pet(new_pet_window, "deltarune-tenna.gif", "tenna-talking.mp3", 100, 100)
        self.pets.append(new_pet)

    def create_spamton(self):
        new_pet_window = tk.Toplevel(self.master)
        new_pet = SpamtonPet(new_pet_window, 300, 100)
        self.pets.append(new_pet)
    
    def create_secret_pet(self):
        # The secret pet is created just like the others.
        new_pet_window = tk.Toplevel(self.master)
        new_pet = SecretPet(new_pet_window, 500, 500)
        self.pets.append(new_pet)

# --- Main Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app_launcher = PetManager(root)
    root.mainloop()