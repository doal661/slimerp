import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3, hashlib, datetime, re, csv, unicodedata

# =============================================================================
# [Iron Vault v9.7] Final Complete (Single DB + Intelligent Search)
# -----------------------------------------------------------------------------
# 0. Env : 파이썬 3.4 호환 목표
# 1. Logic: 단일 DB (vault_master.db) 적용
# 2. Fix: 마이너스 금액 허용 (반품/취소 대응)
# 3. Search: 공백 무시 + 작대기 대통합 + 역순 자동 교정 (Swap)
# =============================================================================

class IronVaultCommander:
    def __init__(self, root):
        self.root = root
        self.root.title("Iron Vault v9.7 (Stable - Intelligent Search)")
        self.root.geometry("1000x700")
        
        self.db_path = "vault_master.db"
        self.init_database()
        
        self.current_view, self.sort_col, self.sort_desc = "erp", "date", True
        self.setup_ui()
        self.load_data()

    def init_database(self):
        """단일 테이블(master_book) 통합 및 검색 최적화(Index)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 1. 테이블 생성 (기존과 동일)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS master_book (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT, corp TEXT, amount INTEGER,
                        t_no TEXT, tax_rate INTEGER, tax INTEGER, item TEXT,
                        hash TEXT UNIQUE, created_at TEXT
                    )
                """)
                
                # ---------------------------------------------------------
                # [추가] 검색 속도 10배 향상을 위한 '인덱스(지름길)' 설치
                # ---------------------------------------------------------
                # 설명: 거래처(corp)와 날짜(date)는 WHERE 절에서 가장 많이 뒤지는 놈들이라
                # 미리 정렬된 지도(Index)를 만들어둡니다. (100만 건 넘어가면 필수)
                
                conn.execute("CREATE INDEX IF NOT EXISTS idx_corp ON master_book(corp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON master_book(date)")
                
        except Exception as e: 
            # 에러 메시지를 좀 더 구체적으로 띄우도록 수정했습니다.
            messagebox.showerror("DB 초기화 오류", f"DB 파일 접근 실패: {str(e)}")



    def setup_ui(self):
        # --- [1] 입력부 ---
        input_frame = tk.LabelFrame(self.root, text=" [ 1. 데이터 박제소 ] ", padx=5, pady=5)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.entries = {}
        fields = [("① 날짜 (2026-01-25)", "date", 0, 0), ("② 거래처명", "corp", 0, 1), ("③ 공급가액", "amount", 0, 2),
                  ("④ T-번호", "t_no", 1, 0), ("⑤ 세율 (10/8)", "tax_rate", 1, 1), ("⑥ 세액", "tax", 1, 2), ("⑦ 품목", "item", 2, 0)]
        
        for txt, key, r, c in fields:
            f = tk.Frame(input_frame); f.grid(row=r, column=c, sticky="we", padx=5, pady=2)
            tk.Label(f, text=txt, anchor="w", font=("MS UI Gothic", 9, "bold")).pack(fill="x")
            e = tk.Entry(f); e.pack(fill="x"); self.entries[key] = e
            if key == "tax_rate": e.insert(0, "10")
            e.bind("<Return>", self.save_transaction) 
            
        for i in range(3): input_frame.grid_columnconfigure(i, weight=1)
        
        tk.Button(input_frame, text="▼ 안전하게 박제하기 (COMMIT) [Enter] ▼", command=self.save_transaction, bg="#2c3e50", fg="white", font=("MS UI Gothic", 9, "bold")).grid(row=3, column=0, columnspan=3, sticky="we", pady=5)

        # --- [2] 검색부 ---
        search_frame = tk.LabelFrame(self.root, text=" [ 2. 통합 검색 필터 ] ", padx=10, pady=5)
        search_frame.pack(fill="x", padx=10, pady=5)

        row1 = tk.Frame(search_frame); row1.pack(fill="x", pady=2)
        tk.Label(row1, text="검색어:", width=8, anchor="e").pack(side="left")
        self.entry_search = tk.Entry(row1, width=20); self.entry_search.pack(side="left", padx=5)
        
        tk.Label(row1, text="날짜:", width=8, anchor="e").pack(side="left")
        self.date_start = tk.Entry(row1, width=12); self.date_start.pack(side="left")
        tk.Label(row1, text="~").pack(side="left")
        self.date_end = tk.Entry(row1, width=12); self.date_end.pack(side="left")

        row2 = tk.Frame(search_frame); row2.pack(fill="x", pady=2)
        tk.Label(row2, text="금액:", width=8, anchor="e").pack(side="left")
        self.amt_min = tk.Entry(row2, width=15); self.amt_min.pack(side="left", padx=5)
        tk.Label(row2, text="~").pack(side="left")
        self.amt_max = tk.Entry(row2, width=15); self.amt_max.pack(side="left")
        
        tk.Button(row2, text="🔍 검색", command=self.load_data, bg="#3498db", fg="white", width=8).pack(side="left", padx=15)
        tk.Button(row2, text="🔄 초기화", command=self.clear_search, width=8).pack(side="left")

        for w in [self.entry_search, self.date_start, self.date_end, self.amt_min, self.amt_max]:
            w.bind("<Return>", self.on_search_enter)

        # --- [3] 결과창 ---
        ctrl = tk.Frame(self.root); ctrl.pack(fill="x", padx=10, pady=5)
        tk.Button(ctrl, text="[ 장부 모드 ]", command=lambda: self.switch_view("erp"), width=12).pack(side="left")
        tk.Button(ctrl, text="[ 인보이스 모드 ]", command=lambda: self.switch_view("inv"), width=12, padx=2).pack(side="left")
        tk.Button(ctrl, text="CSV 내보내기", command=self.export_to_csv, bg="#27ae60", fg="white").pack(side="right")

        tree_frame = tk.Frame(self.root); tree_frame.pack(fill="both", expand=True, padx=10, pady=5)
        sb = ttk.Scrollbar(tree_frame, orient="vertical"); sb.pack(side="right", fill="y")
        self.tree = ttk.Treeview(tree_frame, show="headings", selectmode="browse") 
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.configure(yscrollcommand=sb.set); sb.configure(command=self.tree.yview)

    def on_search_enter(self, event): self.load_data(); return "break"
    def clear_search(self):
        for e in [self.entry_search, self.date_start, self.date_end, self.amt_min, self.amt_max]: e.delete(0, 'end')
        self.load_data()

    def validate_input(self, d):
        try: datetime.datetime.strptime(d["date"], "%Y-%m-%d")
        except: raise ValueError("날짜 형식 오류 (YYYY-MM-DD)")
        # 금액에서 마이너스(-) 허용을 위해 int() 변환만 체크 (regex로 이미 정제됨)
        try: 
            amt = int(d["amount"])
            tax, rate = int(d["tax"]), int(d["tax_rate"])
        except: raise ValueError("금액/세율/세액은 숫자(마이너스 포함)만 가능합니다!")
        if not d["corp"].strip(): raise ValueError("거래처명 필수")
        return amt, tax, rate
        
    def save_transaction(self, event=None):
        try:
            # 1. 데이터 가져오기 및 NFKC 정규화
            d = {k: unicodedata.normalize('NFKC', v.get()) for k, v in self.entries.items()}

            # [A] 날짜 정규화
            d["date"] = "".join(d["date"].split())
            d["date"] = re.sub(r'[\u30FC\uFF0D\u2010-\u2015\u2212/.]', '-', d["date"])

            # [B] 거래처 정규화 (자석 하이픈)
            d["corp"] = d["corp"].strip()
            pattern = r'\s*[-\uFF0D\u2010-\u2015\u2212]\s*'
            d["corp"] = re.sub(pattern, '-', d["corp"])

            # ---------------------------------------------------------------------
            # [C] 숫자 필드 3형제 (금액, 세액, 세율) 대통합 청소
            # ---------------------------------------------------------------------
            # 마이너스 허용 + 좆같은 작대기들(장음, 전각 등) 전부 표준 마이너스(-)로 변환
            for k in ["amount", "tax", "tax_rate"]:
                # 1. 작대기 5형제 -> 표준 마이너스 변환
                val_raw = re.sub(r'[ー－\-\uFF0D\u2010-\u2015\u2212]', '-', d[k])
                # 2. 숫자와 마이너스(-) 빼고 다 삭제 (콤마 등 제거)
                val_clean = re.sub(r'[^\d-]', '', val_raw)
                # 3. 빈칸이거나 '-'만 덩그러니 있으면 '0'으로 처리
                d[k] = val_clean if val_clean not in ["", "-"] else "0"

            # [D] 유효성 검사
            amt, tax, rate = self.validate_input(d)
            if amt is None: return 
            
            # [안전장치] 세율이 8%나 10%가 아니면 재확인 (마이너스 세율도 경고 띄움)
            # 환불이라도 세율 자체가 마이너스인 경우는 드무니까 확인차 물어봅니다.
            if rate not in [8, 10]:
                msg = "세율이 {}%입니다.\n(일반적인 8% 또는 10%가 아닙니다)\n\n정말 이대로 박제할까요?".format(rate)
                if not messagebox.askyesno("세율 경고", msg):
                    return 

            clean_t_no = d["t_no"].upper().strip()
            
            # [E] 해시 생성 (그림자 해시)
            raw_data = "".join(str(x) for x in [d["date"], d["corp"], amt, clean_t_no, tax])
            hash_src = re.sub(r'[\s\u30FC\-\uFF0D\u2010-\u2015\u2212]', '', raw_data)
            
            doc_hash = hashlib.sha256(hash_src.encode()).hexdigest()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with sqlite3.connect(self.db_path) as conn:
                # 1. 해시 중복 체크
                if conn.execute("SELECT 1 FROM master_book WHERE hash=?", (doc_hash,)).fetchone():
                    raise sqlite3.IntegrityError 

                # 2. 내용 중복 경고
                similar = conn.execute("SELECT date FROM master_book WHERE corp=? AND amount=? AND t_no=? AND id != ?", 
                                     (d["corp"], amt, clean_t_no, 0)).fetchone()
                if similar:
                    if not messagebox.askyesno("경고", "과거({})에 동일 기록이 있습니다. 저장할까요?".format(similar[0])): return

                # 3. 데이터 박제
                conn.execute("""
                    INSERT INTO master_book (date, corp, amount, t_no, tax_rate, tax, item, hash, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (d["date"], d["corp"], amt, clean_t_no, rate, tax, d["item"], doc_hash, now))

            # 성공 후 처리
            self.load_data()
            for k, e in self.entries.items(): 
                if k != "tax_rate": e.delete(0, 'end')
            self.entries["date"].focus_set() 
            
        except sqlite3.IntegrityError:
            messagebox.showerror("오류", "DB 무결성 오류 (해시 중복 또는 데이터 손상)\n이미 박제된 데이터일 확률이 높습니다.")
        except PermissionError:
            messagebox.showerror("오류", "파일 권한 문제 – 폴더/파일 읽기/쓰기 권한 확인하세요.\n혹시 DB 파일이 다른 프로그램에서 열려 있나요?")
        except Exception as e:
            messagebox.showerror("오류", "알 수 없는 오류 발생:\n{}".format(str(e)))



    def switch_view(self, mode): self.current_view = mode; self.load_data()
    
    def sort_by(self, col): 
        if self.sort_col == col: self.sort_desc = not self.sort_desc
        else: self.sort_col, self.sort_desc = col, True
        self.load_data()

    def load_data(self):
        # 1. 검색어 및 범위 데이터 가져오기
        kw = self.entry_search.get().strip().split()
        
        # 날짜/금액 범위 정제 (마이너스 허용)
        s_d = re.sub(r'[^\d-]', '-', self.date_start.get().strip())
        e_d = re.sub(r'[^\d-]', '-', self.date_end.get().strip())
        
        s_a_raw = re.sub(r'[ー－\-\uFF0D\u2010-\u2015\u2212]', '-', self.amt_min.get())
        e_a_raw = re.sub(r'[ー－\-\uFF0D\u2010-\u2015\u2212]', '-', self.amt_max.get())
        s_a = re.sub(r'[^\d-]', '', s_a_raw)
        e_a = re.sub(r'[^\d-]', '', e_a_raw)

        # [교정] 시작값이 끝값보다 크면 자동 Swap (사용자 실수 방지)
        if s_d and e_d and s_d > e_d: s_d, e_d = e_d, s_d
        try:
            if s_a and e_a and int(s_a) > int(e_a): s_a, e_a = e_a, s_a
        except: pass

        # 트리뷰 초기화
        for i in self.tree.get_children(): self.tree.delete(i)
        
        # 2. 뷰 모드 설정 (ERP 모드 vs 인보이스 모드)
        if self.current_view == "erp":
            cols = [("ID", "id", 20), ("날짜", "date", 40), ("거래처", "corp", 250), ("가액", "amount", 60), ("생성일시", "created_at", 120)]
            sql_select = "SELECT id, date, corp, amount, created_at FROM master_book"
            # [핵심] 합계 금액(amount+tax)도 검색 대상에 포함!
            search_fields = ["date", "corp", "amount", "item", "(amount+tax)"]
            amt_col = "amount"
        else:
            cols = [("ID", "id", 40), ("T-번호", "t_no", 110), ("날짜", "date", 70), ("거래처", "corp", 110), 
                    ("품목", "item", 130), ("가액", "amount", 110), ("세율", "tax_rate", 40), ("세액", "tax", 100), ("합계", "amount+tax", 110)]
            sql_select = "SELECT id, t_no, date, corp, item, amount, tax_rate, tax, amount+tax FROM master_book"
            # [핵심] 여기도 합계 포함!
            search_fields = ["date", "corp", "t_no", "item", "amount", "tax", "(amount+tax)"]
            amt_col = "(amount+tax)"

        # 컬럼 설정 적용
        self.tree["columns"] = [c[0] for c in cols]
        for ui, db, w in cols:
            self.tree.heading(ui, text=ui, command=lambda c=db: self.sort_by(c))
            self.tree.column(ui, width=w, anchor="e" if "amount" in db or "tax" in db else "center")

        # ---------------------------------------------------------
        # [검색 필터링] 지능형 검색 (공백 무시 + 작대기 대통합)
        # ---------------------------------------------------------
        where, params = [], []
        
        for k in kw:
            # (1) NFKC 정규화 + 모든 공백 제거
            k = unicodedata.normalize('NFKC', k).replace(" ", "")
            
            # (2) 작대기 대통합 (장음 vs 하이픈)
            k_prolong = re.sub(r'[ー－\-\uFF0D\u2010-\u2015\u2212]', 'ー', k)
            k_hyphen = re.sub(r'[ー－\-\uFF0D\u2010-\u2015\u2212]', '-', k)
            variations = list(set([k, k_prolong, k_hyphen]))
            
            sub_query = []
            for f in search_fields:
                for v in variations:
                    # (3) SQL REPLACE: DB 데이터의 공백도 지우고 비교
                    sub_query.append("REPLACE({}, ' ', '') LIKE ?".format(f))
                    params.append("%{}%".format(v))
            
            where.append("(" + " OR ".join(sub_query) + ")")
        
        # 범위 조건 추가
        if s_d: where.append("date >= ?"); params.append(s_d)
        if e_d: where.append("date <= ?"); params.append(e_d)
        if s_a: where.append("{} >= ?".format(amt_col)); params.append(int(s_a))
        if e_a: where.append("{} <= ?".format(amt_col)); params.append(int(e_a))
        
        # 최종 SQL 조립
        sql = sql_select
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY {} {}".format(self.sort_col, 'DESC' if self.sort_desc else 'ASC')

        # 실행
        try:
            with sqlite3.connect(self.db_path) as conn:
                rows = conn.execute(sql, params).fetchall()
                for r in rows:
                    v = list(r)
                    for i, val in enumerate(v):
                        # 천단위 콤마 서식 적용 (정수형 데이터만)
                        if isinstance(val, int): v[i] = "{:,}".format(val)
                    self.tree.insert("", "end", values=v)
        except: pass


    def export_to_csv(self):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = "IronVault_Export_{}.csv".format(timestamp)
        fname = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name, filetypes=[("CSV", "*.csv")])
        if not fname: return

        try:
            with sqlite3.connect(self.db_path) as conn:
                sql = """SELECT id, date, t_no, corp, item, amount, tax_rate, tax, (amount+tax), created_at, hash 
                         FROM master_book ORDER BY date DESC, id DESC"""
                rows = conn.execute(sql).fetchall()
                
            headers = ["ID", "날짜", "티번호", "거래처명", "품목", "공급가액", "세율", "세액", "총액", "생성일시", "해시"]
            with open(fname, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            messagebox.showinfo("완료", "저장되었습니다:\n{}".format(fname))
        except Exception as e: messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    root = tk.Tk(); IronVaultCommander(root); root.mainloop()
