import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date

DB_FILE = 'movie_bookings.db'

# Hardcoded movies and their time slots for simplicity
MOVIES = {
    'Avengers: Endgame': ['10:00 AM', '2:00 PM', '6:00 PM'],
    'Inception': ['11:00 AM', '3:00 PM', '7:00 PM'],
    'The Dark Knight': ['12:00 PM', '4:00 PM', '8:00 PM']
}

# ---------- Database helpers ----------
class DB:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path)
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                UNIQUE(movie, time_slot, customer_name, booking_date)
            )
        ''')
        self.conn.commit()

    def add_booking(self, movie, time_slot, customer_name, booking_date):
        try:
            c = self.conn.cursor()
            c.execute('INSERT INTO bookings (movie, time_slot, customer_name, booking_date) VALUES (?, ?, ?, ?)',
                      (movie, time_slot, customer_name, booking_date))
            self.conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None  # Duplicate booking

    def list_bookings(self):
        c = self.conn.cursor()
        c.execute('SELECT id, movie, time_slot, customer_name, booking_date FROM bookings ORDER BY booking_date DESC')
        return c.fetchall()

    def remove_booking(self, booking_id):
        c = self.conn.cursor()
        c.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
        self.conn.commit()

# ---------- GUI ----------
class MovieBookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Movie Ticket Booking System')
        self.db = DB()

        self._build_ui()

    def _build_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Actions', menu=file_menu)
        file_menu.add_command(label='Book Ticket', command=self._open_book_ticket)
        file_menu.add_command(label='Cancel Booking', command=self._open_cancel_booking)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)

        # Main frame
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill='both', expand=True)

        ttk.Label(main, text='Welcome to the Movie Ticket Booking System!\nUse the Actions menu to book or cancel tickets.').pack(pady=20)

    def _open_book_ticket(self):
        win = tk.Toplevel(self.root)
        win.title('Book Ticket')
        win.geometry('400x400')

        canv = ttk.Frame(win, padding=8)
        canv.pack(fill='both', expand=True)

        # Movie selection (radio buttons)
        ttk.Label(canv, text='Select Movie:').pack(anchor='w', pady=(0,5))
        self.movie_var = tk.StringVar()
        for movie in MOVIES.keys():
            ttk.Radiobutton(canv, text=movie, variable=self.movie_var, value=movie).pack(anchor='w')

        # Time slot selection (radio buttons, initially disabled)
        ttk.Label(canv, text='Select Time Slot:').pack(anchor='w', pady=(10,5))
        self.time_var = tk.StringVar()
        self.time_frame = ttk.Frame(canv)
        self.time_frame.pack(anchor='w')
        # Time slots will be populated when movie is selected

        # Bind movie selection to update time slots
        self.movie_var.trace_add('write', lambda *args: self._update_time_slots())

        # Customer name
        ttk.Label(canv, text='Customer Name:').pack(anchor='w', pady=(10,5))
        self.name_entry = ttk.Entry(canv)
        self.name_entry.pack(fill='x')

        # Booking date (default to today)
        ttk.Label(canv, text='Booking Date (YYYY-MM-DD):').pack(anchor='w', pady=(10,5))
        self.date_entry = ttk.Entry(canv)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.pack(fill='x')

        # Buttons
        btn_frame = ttk.Frame(win, padding=(0,8))
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text='Book', command=lambda: self._confirm_book(win)).pack(side='left', padx=(0,6))
        ttk.Button(btn_frame, text='Cancel', command=win.destroy).pack(side='left')

    def _update_time_slots(self):
        # Clear existing time slots
        for widget in self.time_frame.winfo_children():
            widget.destroy()

        movie = self.movie_var.get()
        if movie in MOVIES:
            for slot in MOVIES[movie]:
                ttk.Radiobutton(self.time_frame, text=slot, variable=self.time_var, value=slot).pack(anchor='w')

    def _confirm_book(self, win):
        movie = self.movie_var.get()
        time_slot = self.time_var.get()
        name = self.name_entry.get().strip()
        b_date = self.date_entry.get().strip()

        if not movie or not time_slot or not name or not b_date:
            messagebox.showerror('Error', 'Please fill all fields.')
            return

        try:
            date.fromisoformat(b_date)
        except ValueError:
            messagebox.showerror('Error', 'Invalid date format. Use YYYY-MM-DD.')
            return

        # Confirmation dialog
        if messagebox.askyesno('Confirm Booking', f'Book ticket for "{movie}" at {time_slot} on {b_date} for {name}?'):
            res = self.db.add_booking(movie, time_slot, name, b_date)
            if res is None:
                messagebox.showwarning('Duplicate', 'This booking already exists.')
            else:
                messagebox.showinfo('Success', 'Ticket booked successfully!')
                win.destroy()

    def _open_cancel_booking(self):
        bookings = self.db.list_bookings()
        if not bookings:
            messagebox.showinfo('No Bookings', 'No bookings found.')
            return

        win = tk.Toplevel(self.root)
        win.title('Cancel Booking')
        win.geometry('500x400')

        canv = ttk.Frame(win, padding=8)
        canv.pack(fill='both', expand=True)

        # Listbox for bookings
        ttk.Label(canv, text='Select a booking to cancel:').pack(anchor='w')
        self.booking_listbox = tk.Listbox(canv, height=15)
        self.booking_listbox.pack(fill='both', expand=True)

        for bid, movie, slot, name, b_date in bookings:
            self.booking_listbox.insert(tk.END, f'{b_date} - {movie} ({slot}) - {name} [ID: {bid}]')

        # Buttons
        btn_frame = ttk.Frame(win, padding=(0,8))
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text='Cancel Selected', command=lambda: self._confirm_cancel(win)).pack(side='left', padx=(0,6))
        ttk.Button(btn_frame, text='Close', command=win.destroy).pack(side='left')

    def _confirm_cancel(self, win):
        sel = self.booking_listbox.curselection()
        if not sel:
            messagebox.showinfo('No Selection', 'Please select a booking to cancel.')
            return

        idx = sel[0]
        booking_text = self.booking_listbox.get(idx)
        # Extract ID from text (hacky, but works for this simple app)
        bid = int(booking_text.split('[ID: ')[1].rstrip(']'))

        if messagebox.askyesno('Confirm Cancellation', f'Cancel booking: {booking_text}?'):
            self.db.remove_booking(bid)
            messagebox.showinfo('Success', 'Booking cancelled successfully!')
            win.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = MovieBookingApp(root)
    root.mainloop()
