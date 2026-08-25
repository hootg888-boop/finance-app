import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
import os

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("โปรแกรมจัดการรายรับ-รายจ่าย พร้อม AI วิเคราะห์")
        self.root.geometry("850x650")
        self.root.configure(bg="#f4f4f9")

        # Create database in the same directory as the script
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance_data.db")
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

        self.current_room_id = None

        self.setup_ui()
        self.load_rooms()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms (id)
            )
        ''')
        self.conn.commit()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Left Panel (Rooms)
        self.left_panel = tk.Frame(self.root, width=250, bg="#2c3e50")
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.left_panel, text="แฟ้มข้อมูล (Rooms)", bg="#2c3e50", fg="white", font=("Arial", 14, "bold")).pack(pady=15)
        
        self.room_listbox = tk.Listbox(self.left_panel, font=("Arial", 12), bg="#34495e", fg="white", selectbackground="#1abc9c", borderwidth=0, highlightthickness=0)
        self.room_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.room_listbox.bind('<<ListboxSelect>>', self.on_room_select)

        btn_frame = tk.Frame(self.left_panel, bg="#2c3e50")
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tk.Button(btn_frame, text="➕ สร้างห้อง", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, command=self.add_room).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(btn_frame, text="🗑️ ลบห้อง", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, command=self.delete_room).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Right Panel (Transactions)
        self.right_panel = tk.Frame(self.root, bg="#f4f4f9")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.room_title = tk.Label(self.right_panel, text="⬅️ เลือกห้องทางซ้ายเพื่อดูข้อมูล", font=("Arial", 16, "bold"), bg="#f4f4f9", fg="#2c3e50")
        self.room_title.pack(pady=(0, 15))

        # Input Area
        input_frame = tk.Frame(self.right_panel, bg="#ffffff", padx=15, pady=15, relief=tk.RIDGE, bd=1)
        input_frame.pack(fill=tk.X, pady=5)

        tk.Label(input_frame, text="ประเภท:", bg="#ffffff", font=("Arial", 10)).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.type_var = tk.StringVar(value="รายรับ")
        self.type_dropdown = ttk.Combobox(input_frame, textvariable=self.type_var, values=["รายรับ", "รายจ่าย"], state="readonly", width=10)
        self.type_dropdown.grid(row=0, column=1, padx=5)

        tk.Label(input_frame, text="จำนวนเงิน (บาท):", bg="#ffffff", font=("Arial", 10)).grid(row=0, column=2, padx=5, sticky=tk.W)
        self.amount_entry = ttk.Entry(input_frame, width=12)
        self.amount_entry.grid(row=0, column=3, padx=5)

        tk.Label(input_frame, text="รายละเอียด:", bg="#ffffff", font=("Arial", 10)).grid(row=0, column=4, padx=5, sticky=tk.W)
        self.desc_entry = ttk.Entry(input_frame, width=25)
        self.desc_entry.grid(row=0, column=5, padx=5)

        tk.Button(input_frame, text="บันทึก", bg="#3498db", fg="white", font=("Arial", 10, "bold"), relief=tk.FLAT, command=self.add_transaction).grid(row=0, column=6, padx=15)

        # Transaction Table
        columns = ("id", "date", "type", "description", "amount")
        self.tree = ttk.Treeview(self.right_panel, columns=columns, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="วัน/เวลา")
        self.tree.heading("type", text="ประเภท")
        self.tree.heading("description", text="รายการ")
        self.tree.heading("amount", text="จำนวนเงิน")
        
        self.tree.column("id", width=0, stretch=tk.NO)
        self.tree.column("date", width=120, anchor=tk.CENTER)
        self.tree.column("type", width=80, anchor=tk.CENTER)
        self.tree.column("description", width=250)
        self.tree.column("amount", width=100, anchor=tk.E)
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=15)
        
        # Tags for coloring rows
        self.tree.tag_configure("income", foreground="#27ae60")
        self.tree.tag_configure("expense", foreground="#c0392b")

        # AI Analysis Button
        tk.Button(self.right_panel, text="🤖 ให้ AI วิเคราะห์การเงินของห้องนี้", bg="#9b59b6", fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT, pady=10, command=self.ai_analyze).pack(fill=tk.X)

    def load_rooms(self):
        self.room_listbox.delete(0, tk.END)
        self.rooms = []
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM rooms")
        for row in cursor.fetchall():
            self.rooms.append(row)
            self.room_listbox.insert(tk.END, f"📁 {row[1]}")

    def add_room(self):
        name = simpledialog.askstring("สร้างห้องใหม่", "กรุณาตั้งชื่อห้อง/บัญชี:")
        if name:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO rooms (name) VALUES (?)", (name,))
            self.conn.commit()
            self.load_rooms()

    def delete_room(self):
        selection = self.room_listbox.curselection()
        if not selection:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกห้องที่ต้องการลบจากรายการทางซ้ายมือ")
            return
        
        index = selection[0]
        room_id, room_name = self.rooms[index]
        
        if messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบห้อง '{room_name}' พร้อมข้อมูลรายรับ-รายจ่ายทั้งหมดหรือไม่? (ไม่สามารถกู้คืนได้)"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE room_id = ?", (room_id,))
            cursor.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
            self.conn.commit()
            self.load_rooms()
            self.current_room_id = None
            self.room_title.config(text="⬅️ เลือกห้องทางซ้ายเพื่อดูข้อมูล")
            self.load_transactions()

    def on_room_select(self, event):
        selection = self.room_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_room_id, room_name = self.rooms[index]
            self.room_title.config(text=f"📊 ข้อมูลของห้อง: {room_name}")
            self.load_transactions()

    def add_transaction(self):
        if not self.current_room_id:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกหรือสร้างห้องก่อนทำการบันทึก")
            return
            
        trans_type = self.type_var.get()
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError("จำนวนเงินต้องมากกว่า 0")
        except ValueError:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกจำนวนเงินเป็นตัวเลขที่ถูกต้อง (เช่น 150.50)")
            return
            
        desc = self.desc_entry.get()
        if not desc:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกรายละเอียดรายการ")
            return

        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO transactions (room_id, type, amount, description, date) VALUES (?, ?, ?, ?, ?)",
                       (self.current_room_id, trans_type, amount, desc, date))
        self.conn.commit()
        
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.load_transactions()

    def load_transactions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not self.current_room_id:
            return
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, date, type, description, amount FROM transactions WHERE room_id = ? ORDER BY date DESC", (self.current_room_id,))
        for row in cursor.fetchall():
            row_id, date, trans_type, desc, amount = row
            formatted_amount = f"{amount:,.2f}"
            tag = "income" if trans_type == "รายรับ" else "expense"
            self.tree.insert("", tk.END, values=(row_id, date, trans_type, desc, formatted_amount), tags=(tag,))

    def ai_analyze(self):
        if not self.current_room_id:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกห้องเพื่อทำการวิเคราะห์")
            return
            
        cursor = self.conn.cursor()
        cursor.execute("SELECT type, amount, description FROM transactions WHERE room_id = ?", (self.current_room_id,))
        transactions = cursor.fetchall()
        
        if not transactions:
            messagebox.showinfo("AI Analysis", "ยังไม่มีข้อมูลในห้องนี้เพียงพอสำหรับการวิเคราะห์")
            return
            
        total_income = sum(t[1] for t in transactions if t[0] == "รายรับ")
        total_expense = sum(t[1] for t in transactions if t[0] == "รายจ่าย")
        balance = total_income - total_expense
        
        analysis = f"สรุปภาพรวมทางการเงิน:\n"
        analysis += "-"*40 + "\n"
        analysis += f"💵 รายรับรวม:   {total_income:,.2f} บาท\n"
        analysis += f"💸 รายจ่ายรวม:  {total_expense:,.2f} บาท\n"
        analysis += "-"*40 + "\n"
        analysis += f"💰 ยอดคงเหลือ:  {balance:,.2f} บาท\n\n\n"
        
        analysis += "🤖 AI Insights (ข้อคิดเห็นจากระบบ):\n"
        
        if total_income == 0:
            analysis += "⚠️ ข้อมูลของคุณมีแต่รายจ่าย แนะนำให้หาช่องทางเพิ่มรายได้ หรือระมัดระวังการใช้เงินในส่วนนี้"
        elif total_expense == 0:
            analysis += "✨ สุดยอด! คุณไม่มีรายจ่ายในหมวดหมู่นี้เลย การเก็บออมของคุณอยู่ในเกณฑ์ดีเยี่ยม"
        else:
            expense_ratio = (total_expense / total_income) * 100
            analysis += f"📈 สัดส่วนรายจ่ายคิดเป็น {expense_ratio:.1f}% ของรายรับ\n\n"
            
            if expense_ratio > 90:
                analysis += "🚨 วิกฤต! คุณใช้จ่ายเกือบเท่ารายรับที่หามาได้ มีความเสี่ยงสูงที่จะเป็นหนี้ แนะนำให้ตรวจสอบ 'รายการ' ด้านบนและลดรายจ่ายที่ไม่จำเป็นด่วน!"
            elif expense_ratio > 60:
                analysis += "⚠️ ควรระวัง: คุณมีค่าใช้จ่ายค่อนข้างสูง แนะนำให้ตั้งเป้าหมายลดรายจ่ายลงอีกประมาณ 10-20% เพื่อเพิ่มสภาพคล่อง"
            elif expense_ratio > 30:
                analysis += "✅ สุขภาพการเงินดี: คุณมีการบริหารรายจ่ายอยู่ในระดับที่เหมาะสม มีเงินเหลือเก็บออม"
            else:
                analysis += "🌟 สุขภาพการเงินยอดเยี่ยม!: คุณมีการใช้จ่ายที่ต่ำมากเมื่อเทียบกับรายรับ สามารถนำเงินที่เหลือไปลงทุนหรือฝากประจำเพื่อสร้างผลกำไรเพิ่มเติมได้"
                
        # Top expense finder
        expenses = [t for t in transactions if t[0] == "รายจ่าย"]
        if expenses:
            top_expense = max(expenses, key=lambda x: x[1])
            analysis += f"\n\n🔍 รายการใช้จ่ายที่สูงที่สุดของคุณคือ: '{top_expense[2]}' จำนวน {top_expense[1]:,.2f} บาท"

        messagebox.showinfo("AI Financial Analysis & Insights", analysis)

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
