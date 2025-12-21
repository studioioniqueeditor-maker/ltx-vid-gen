import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import base64
import os
import threading
from PIL import Image, ImageTk

class LTXGui:
    def __init__(self, root):
        self.root = root
        self.root.title("LTX Video Generator Client")
        self.root.geometry("600x750")
        
        # Configuration Variables
        self.api_endpoint_var = tk.StringVar(value="https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync")
        self.api_key_var = tk.StringVar(value="")
        self.prompt_var = tk.StringVar(value="A cinematic shot of a futuristic city")
        self.image_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        
        # --- UI Layout ---
        
        # API Config Section
        config_frame = tk.LabelFrame(root, text="API Configuration", padx=10, pady=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(config_frame, text="Endpoint URL:").pack(anchor="w")
        tk.Entry(config_frame, textvariable=self.api_endpoint_var).pack(fill="x")
        
        tk.Label(config_frame, text="API Key:").pack(anchor="w")
        tk.Entry(config_frame, textvariable=self.api_key_var, show="*").pack(fill="x")
        
        # Input Section
        input_frame = tk.LabelFrame(root, text="Generation Input", padx=10, pady=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(input_frame, text="Prompt:").pack(anchor="w")
        tk.Entry(input_frame, textvariable=self.prompt_var).pack(fill="x")
        
        tk.Label(input_frame, text="Input Image:").pack(anchor="w", pady=(10, 0))
        img_select_frame = tk.Frame(input_frame)
        img_select_frame.pack(fill="x")
        tk.Entry(img_select_frame, textvariable=self.image_path_var, state="readonly").pack(side="left", fill="x", expand=True)
        tk.Button(img_select_frame, text="Browse", command=self.browse_image).pack(side="right", padx=(5, 0))
        
        # Image Preview
        self.preview_label = tk.Label(input_frame, text="No image selected")
        self.preview_label.pack(pady=10)
        
        # Generate Button
        self.generate_btn = tk.Button(root, text="Generate Video (30fps / 5s)", command=self.start_generation, bg="green", fg="black", height=2)
        self.generate_btn.pack(fill="x", padx=10, pady=10)
        
        # Status
        tk.Label(root, textvariable=self.status_var, wraplength=580).pack(pady=5)
        
    def browse_image(self):
        filename = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if filename:
            self.image_path_var.set(filename)
            self.load_preview(filename)
            
    def load_preview(self, path):
        try:
            img = Image.open(path)
            # Resize for preview
            img.thumbnail((300, 200))
            self.photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.photo, text="")
        except Exception as e:
            self.preview_label.config(text=f"Error loading preview: {e}", image="")

    def start_generation(self):
        # Validation
        if not self.api_key_var.get():
            messagebox.showerror("Error", "Please enter your RunPod API Key")
            return
        if "YOUR_ENDPOINT_ID" in self.api_endpoint_var.get():
            messagebox.showwarning("Warning", "Please check your Endpoint URL")
            return
        if not self.image_path_var.get():
            messagebox.showerror("Error", "Please select an image")
            return
            
        # Disable UI
        self.generate_btn.config(state="disabled", text="Generating... (This may take a few minutes)")
        self.status_var.set("Uploading and processing...")
        
        # Run in thread
        thread = threading.Thread(target=self.run_generation)
        thread.start()
        
    def run_generation(self):
        try:
            # 1. Encode Image
            image_path = self.image_path_var.get()
            with open(image_path, "rb") as img_file:
                b64_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            # 2. Prepare Payload
            payload = {
                "input": {
                    "prompt": self.prompt_var.get(),
                    "image_base64": b64_image,
                    "width": 1280,
                    "height": 720,
                    "num_frames": 151,  # 30fps * 5s = 150 (using 151 for safety)
                    "num_steps": 30,    # Good quality steps
                    "fps": 30
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key_var.get()}",
                "Content-Type": "application/json"
            }
            
            # 3. Send Request
            self.update_status("Sending request to RunPod...")
            response = requests.post(
                self.api_endpoint_var.get(),
                json=payload,
                headers=headers,
                timeout=600 # 10 minute timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP Error {response.status_code}: {response.text}")
                
            data = response.json()
            
            # 4. Process Response
            if "error" in data:
                raise Exception(f"API Error: {data['error']}")
            
            # Handle RunPod response structure
            output_data = data.get("output", {})
            # If wrapped again or direct
            if isinstance(output_data, dict):
                 video_b64 = output_data.get("video_base64")
            else:
                 # sometimes simple handlers return direct, but runpod wraps
                 video_b64 = None 
                 
            # Fallback checks
            if not video_b64 and "video_base64" in data:
                video_b64 = data["video_base64"]
                
            if not video_b64:
                raise Exception(f"No video found in response. Keys: {data.keys()}")
                
            # 5. Save Video
            output_filename = "output_video.mp4"
            with open(output_filename, "wb") as f:
                f.write(base64.b64decode(video_b64))
                
            self.update_status(f"Success! Video saved to {os.path.abspath(output_filename)}")
            messagebox.showinfo("Success", f"Video saved to:\n{os.path.abspath(output_filename)}")
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            # Re-enable UI
            self.root.after(0, lambda: self.generate_btn.config(state="normal", text="Generate Video (30fps / 5s)"))

    def update_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

if __name__ == "__main__":
    root = tk.Tk()
    app = LTXGui(root)
    root.mainloop()
