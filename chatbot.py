import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import requests
import io
import textwrap
import speech_recognition as sr
import json


# Flask API URLs
BASE_URL = 'http://127.0.0.1:5000/api'

# Display loading message
def display_loading_message(message_label):
    message_label.config(text="Loading...")
    root.update_idletasks()

# Clear loading message
def clear_loading_message(message_label):
    message_label.config(text="")

# Clear search bar and order entry field when a new search is initiated
def clear_search_inputs():
    search_entry.delete(0, tk.END)
    order_entry.delete(0, tk.END)
   
 
    
    
def load_intent_replies():
    try:
        with open("intent_replies.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Error: intent_replies.json file not found.")
        return {}
    
    # Handle FAQ (intent-based) search
def handle_faq_search():
    query = search_entry.get().strip()
    if not query:
        messagebox.showwarning("Input Error", "Please enter a query.")
        return

    user_query_label = tk.Label(scrollable_frame, text=f"You: {query}", font=("Arial", 12), wraplength=300, bg="#F0F0F0", fg="#000000", padx=10, pady=5)
    user_query_label.pack(anchor="e", pady=5)

    intent_replies = load_intent_replies()
    if query.lower() in intent_replies:
        display_text_response(intent_replies[query.lower()])
        clear_search_inputs()
    else:
        tk.Label(scrollable_frame, text="No response found for the searched query", font=("Arial", 14), fg="black").pack(anchor="w", pady=10)
        clear_search_inputs()
# Handle text search
def handle_text_search(query):
    if query.strip():
        user_query_label = tk.Label(scrollable_frame, text=f"You: {query}", font=("Arial", 12), wraplength=300, bg="#F0F0F0", fg="#000000", padx=10, pady=5)
        user_query_label.pack(anchor="e", pady=5)

    
    if query.strip() == "Search by product name...":
        messagebox.showwarning("Input Error", "Please enter a search query.")
        return

    # Clear previous content and order entry field
    clear_search_inputs()
    display_loading_message(status_label)
    search_entry.bind("<Return>", lambda event: handle_text_search(search_entry.get()))
    scrollable_frame.bind("<MouseWheel>", lambda event: scrollable_frame.yview_scroll(-1 * (event.delta // 120), "units"))



    response = requests.get(f"{BASE_URL}/search", params={"query": query})
    clear_loading_message(status_label)
    if response.status_code == 200:
        results = response.json()
        # Display search results heading
        tk.Label(scrollable_frame, text="Search Results", font=("Arial", 14, "bold"), fg="BLACK").pack(anchor="w", pady=(10, 0))
        display_product_results(results['search_results'])
        
        # Display sentiment recommendations heading
        if 'category_recommendations' in results:
            display_category_recommendations(results['category_recommendations'])
    else:
        messagebox.showerror("Search Error", response.json().get("error", "No results found."))
        tk.Label(scrollable_frame, text="No results found. Try another search !", font=("Arial", 14), fg="black").pack(anchor="w", pady=10)
        return

# Display text responses for intents
def display_text_response(response):
    response_label = tk.Label(scrollable_frame, text=response, font=("Arial", 12), wraplength=300, bg="#DFF6FF", fg="#00509E", relief="solid", padx=10, pady=10)
    response_label.pack(anchor="w", pady=10)

# Display product results
def display_product_results(products):
    
    for product in products:
        result_frame = tk.Frame(scrollable_frame, borderwidth=2, relief="solid", padx=10, pady=10, height=200, bg="#FFFFFF")
        result_frame.pack(pady=10, padx=10, fill="x", anchor="w")  # Adjust height for more length

        if product['image_url']:
            image_response = requests.get(product['image_url'])
            if image_response.status_code == 200:
                image_data = image_response.content
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((100, 100))
                img = ImageTk.PhotoImage(image)
                img_label = tk.Label(result_frame, image=img)
                img_label.image = img
                img_label.pack(side="left")

        truncated_title = textwrap.shorten(product.get('title', 'No Title Available'), width=60)  # Default if title is missing
        truncated_review = textwrap.shorten(product.get('top_review', 'No Review Available'), width=100)  # Default review if missing

        tk.Label(result_frame, text=f"Title: {truncated_title}", font=("Arial", 10, "bold"), wraplength=300, bg="white", fg="#3B2F2F").pack(anchor="w")
        tk.Label(result_frame, text=f"Review: {truncated_review}", wraplength=400, bg="white", fg="#3B2F2F").pack(anchor="w")
        price = str(product.get('initial_price', 'N/A')).replace('[', '').replace(']', '').replace('\'', '').replace('\"', '')
        tk.Label(result_frame, text=f"Price: {price}", font=("Arial", 10), bg="white", fg="#3B2F2F").pack(anchor="w")
       
        
        # View product link
        def open_product_callback(url):
            open_product_page(url)

        view_link = tk.Label(result_frame, text="View Product", fg="BLACK", cursor="hand2", font=("Arial", 10, "underline"))
        view_link.pack(anchor="w")
        view_link.bind("<Button-1>", lambda e, url=product['url']: open_product_callback(url))
        
def display_category_recommendations(products):
    tk.Label(scrollable_frame, text="Recommendations Based on Sentiment Analysis", 
             font=("Arial", 14, "bold"), fg="BLACK").pack(anchor="w", pady=(20, 10))
    
    for product in products:
        result_frame = tk.Frame(scrollable_frame, borderwidth=2, relief="solid", 
                                 padx=10, pady=10, bg="#F9F9F9")
        result_frame.pack(pady=10, padx=10, fill="x", anchor="w")

        # Display product image or placeholder
        if product.get('image_url'):
            try:
                image_response = requests.get(product['image_url'], timeout=5)
                image_response.raise_for_status()
                image_data = image_response.content
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((100, 100))
                img = ImageTk.PhotoImage(image)
                img_label = tk.Label(result_frame, image=img)
                img_label.image = img
                img_label.pack(side="left", padx=(0, 10))
            except (requests.RequestException, IOError):
                # Default placeholder
                placeholder = Image.open("noimages.jpg")
                placeholder.thumbnail((100, 100))
                img = ImageTk.PhotoImage(placeholder)
                img_label = tk.Label(result_frame, image=img)
                img_label.image = img
                img_label.pack(side="left", padx=(0, 10))

        # Product details
        truncated_title = textwrap.shorten(product.get('title', 'No Title Available'), width=60)
        tk.Label(result_frame, text=f"Title: {truncated_title}", 
                 font=("Arial", 10, "bold"), wraplength=300, bg="white", fg="#3B2F2F").pack(anchor="w")
        
        truncated_review = textwrap.shorten(product.get('top_review', 'No Review Available'), width=80)
        tk.Label(result_frame, text=f"Review: {truncated_review}", 
                 font=("Arial", 10), wraplength=300, bg="white", fg="#3B2F2F").pack(anchor="w")
        
        tk.Label(result_frame, text=f"Sentiment Score: {product.get('sentiment_score', 'N/A')}", 
                 font=("Arial", 10), bg="white", fg="#3B2F2F").pack(anchor="w")
        tk.Label(result_frame, text=f"Rating: {product.get('rating', '0')}", font=("Arial", 10), bg="white", fg="#3B2F2F").pack(anchor="w")
        categories = str(product.get('category', 'N/A')).replace('[', '').replace(']', '').replace('\'', '').replace('\"', '')
        tk.Label(result_frame, text=f"Categories: {categories}", font=("Arial", 10), bg="white", fg="#3B2F2F").pack(anchor="w")

        # View Product link
        def open_product_callback(url):
            open_product_page(url)

        view_link = tk.Label(result_frame, text="View Product", fg="blue", cursor="hand2", font=("Arial", 10, "underline"))
        view_link.pack(anchor="w")
        view_link.bind("<Button-1>", lambda e, url=product.get('url', '#'): open_product_callback(url))


# Handle image search and order status
def handle_image_search():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.webp")])
    if not file_path:
        return

    clear_search_inputs()  # Clear previous search inputs
    display_loading_message(status_label)
    with open(file_path, "rb") as file:
        response = requests.post(f"{BASE_URL}/image-search", files={"image": file})
    clear_loading_message(status_label)

    if response.status_code == 200:
        results = response.json()
        tk.Label(scrollable_frame, text="Image Search Results", font=("Arial", 14, "bold"), fg="black").pack(anchor="w", pady=(10, 0))
        display_product_results(results['search_results'])
    else:
        messagebox.showerror("Search Error", response.json().get("error", "No results found."))
        tk.Label(scrollable_frame, text="No results found. Try another search ", font=("Arial", 14), fg="black").pack(anchor="w", pady=10)
        return
    

                    
                    
def handle_order_status_search(order_no):
    if order_no.strip():
        user_query_label = tk.Label(scrollable_frame, text=f"You: {order_no}", font=("Arial", 12), wraplength=300, bg="#F0F0F0", fg="#000000", padx=10, pady=5)
        user_query_label.pack(anchor="e", pady=5)
    if order_no.strip() == "Enter order number...":
        messagebox.showwarning("Input Error", "Please enter an order number.")
        return

    clear_search_inputs()  # Clear previous content
    display_loading_message(status_label)
    response = requests.get(f"{BASE_URL}/order-status", params={"orderNo": order_no})
    clear_loading_message(status_label)

    if response.status_code == 200:
        order_details = response.json()
        display_order_details(order_details)
    else:
        messagebox.showerror("Order Status Error", response.json().get("error", "Order not found."))
        tk.Label(scrollable_frame, text="No results found. Try a different order number!", font=("Arial", 14), fg="black").pack(anchor="w", pady=10)
        return

# Function to clear chat history
def clear_chat_history():
    # Destroy all widgets in the scrollable_frame to clear chat history
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

def display_order_details(details):
    tk.Label(scrollable_frame, text="Your Order Details", font=("Arial", 14, "bold"), fg="black").pack(anchor="w", pady=(10, 0))
    result_frame = tk.Frame(scrollable_frame, borderwidth=2, relief="solid", padx=10, pady=10, bg="WHITE")
    
    result_frame.pack(pady=10, padx=10, fill="x")

    orderno=details.get('order_no','xxxxx')
    date_of_order=details.get('order_date','unknown')
    status = details.get('order_status', 'Unknown')
    shipaddress=details.get('ship_state','Unknown')
    Currentlocation=details.get('current_location','Unknown')
    date_of_delivery=details.get('delivery_date','unknown')
        # Display search results heading
    

    # Display order details
    tk.Label(result_frame, text=f"ORDER NO: {orderno}", font=("Arial", 10), fg="#3B2F2F").pack(anchor="w")
    tk.Label(result_frame, text=f"Date of Order: {date_of_order}", font=("Arial", 10),   fg="#3B2F2F").pack(anchor="w")
    tk.Label(result_frame, text=f"Expected Delivery: {date_of_delivery}", font=("Arial", 14, "bold"), fg="blue").pack(anchor="w")
    tk.Label(result_frame, text=f"Shipping Address: {shipaddress}", font=("Arial", 10), fg="#3B2F2F").pack(anchor="w")
    tk.Label(result_frame, text=f"Order Status: {status}", font=("Arial", 14, "bold"), fg="green").pack(anchor="w")
    tk.Label(result_frame, text=f"Current Location of order: {Currentlocation}", font=("Arial", 10),   fg="#3B2F2F").pack(anchor="w")


# Voice search function
def handle_voice_search():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            status_label.config(text="Listening...")
            root.update_idletasks()
            audio = recognizer.listen(source, timeout=5)
            query = recognizer.recognize_google(audio)
            status_label.config(text=f"You said: {query}")
            search_entry.delete(0, tk.END)
            search_entry.insert(0, query)

            intent_replies = load_intent_replies()
            if query.lower() in intent_replies:
              display_text_response(intent_replies[query.lower()])
              clear_search_inputs()
            else:
                handle_text_search(query)
            


        except sr.UnknownValueError:
            status_label.config(text="Sorry, I couldn't understand that. Please try again.")
            display_text_response("Sorry, I couldn't understand that.")
        
        except sr.RequestError:
            messagebox.showerror("Error", "Could not request results, please check your internet connection.")
            status_label.config(text="Could not request results, please check your internet connection")

        except Exception as e:
            status_label.config(text=f"Error: {str(e)}")
            display_text_response(f"Error: {str(e)}")
            
        finally:
            status_label.config(text="")

            


# Open product page in browser

def open_product_page(url):

    import webbrowser

    webbrowser.open(url)


root = tk.Tk()
root.title("Smart Bot")
root.geometry("1000x800")
root.config(bg="#3B2F2F")

# Create a frame for the whole background (fill the entire window)
background_frame = tk.Frame(root, bg="#3B2F2F")
background_frame.pack(fill="both", expand=True)

# Scrollable canvas for chat interface
canvas = tk.Canvas(background_frame, bg="#ffffff")
canvas.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(background_frame, orient="vertical", command=canvas.yview)
scrollbar.pack(side="right", fill="y")

canvas.config(yscrollcommand=scrollbar.set)

scrollable_frame = tk.Frame(canvas, bg="white")
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Bind canvas resizing
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Status label for loading and search updates
status_label = tk.Label(background_frame, text="", font=("Arial", 12), fg="#FFFFFF", bg="#3B2F2F")
status_label.pack(pady=10)

# General search label above the product search box
general_search_label = tk.Label(background_frame, text="General Search", font=("Arial", 12, "bold"), fg="#FFFFFF",bg="#3B2F2F") 
general_search_label.pack(pady=(10, 0))

# Product search box
search_entry = tk.Entry(background_frame, font=("Arial", 12), bg="#F0F0F0", fg="#000000")
search_entry.pack(pady=(10, 0))

# Frame for buttons
button_frame = tk.Frame(background_frame, bg="#3B2F2F", padx=20, pady=20)
button_frame.pack(pady=(10, 0))

# Buttons for different searches
search_button = tk.Button(button_frame, text="Search by Product Title", font=("Arial", 12), bg="#D8AF3D", command=lambda: handle_text_search(search_entry.get()))
search_button.pack(pady=5, fill="x")

faq_search_button = tk.Button(button_frame, text="FAQ Search", font=("Arial", 12), bg="#D8AF3D", command=handle_faq_search)
faq_search_button.pack(pady=5, fill="x")

image_search_button = tk.Button(button_frame, text="Search by Image", font=("Arial", 12), bg="#D8AF3D", command=handle_image_search)
image_search_button.pack(pady=5, fill="x")

voice_search_button = tk.Button(button_frame, text="Search by Audio", font=("Arial", 12), bg="#D8AF3D", command=handle_voice_search)
voice_search_button.pack(pady=5, fill="x")

# Order search label above the order number search box
order_search_label = tk.Label(background_frame, text="Order Status Search", font=("Arial", 12, "bold"), fg="#FFFFFF",bg="#3B2F2F")
order_search_label.pack(pady=(10, 0))  # Adds some padding for space

# Order number entry (already existing order_entry)
order_entry = tk.Entry(background_frame, font=("Arial", 12), bg="#F0F0F0", fg="#000000")
order_entry.pack(pady=(10, 0))

# Order status search button
order_status_button = tk.Button(background_frame, text="Search Order Status", font=("Arial", 12), bg="#D8AF3D", command=lambda: handle_order_status_search(order_entry.get()))
order_status_button.pack(pady=5)

# Clear chat history button
clear_button = tk.Button(background_frame, text="Clear Results", font=("Arial", 12), command=clear_chat_history, bg="#D8AF3D")
clear_button.pack(side="bottom", pady=10)

root.mainloop()