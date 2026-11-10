import json
from urllib.parse import urlparse, parse_qs
import sqlite3

db = sqlite3.connect("PR3_DataBase.db")

cursor = db.cursor()


def do_GET(self):
    if self.path == "/":
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        self.wfile.write(bytes(
            "<html><body><h1>ОБМЕННИК ВАЛЮТ</h1></body></html>",
            "utf-8"))

    elif self.path == "/currencies":
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            cursor.execute("SELECT * FROM Currencies")
            currencies_data = cursor.fetchall()
            currencies_json = json.dumps(currencies_data)
            self.wfile.write(currencies_json.encode("utf-8"))
        except Exception:
            self.send_error(500, "Database is unavailable")


    elif self.path.startswith("/currency/"):
        name_cur = self.path.split("/")[-1]
        if len(name_cur) == 0:
            self.send_error(400, "Currency code is missing")


        else:
            cursor.execute("SELECT * FROM Currencies WHERE Code = ?",
                                            (name_cur,))
            currency = cursor.fetchone()

            if currency is None:
                self.send_error(404, "Currency not found")
            else:
                try:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    cur_response_json = json.dumps(currency)

                    self.wfile.write(cur_response_json.encode("utf-8"))
                except Exception:
                    self.send_error(500, "Database is unavailable")

    elif self.path == "/exchangeRates":
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            cursor.execute("""
                        SELECT
                            ExchangeRates.ID,
                            BaseCurrency.ID,
                            BaseCurrency.FullName,
                            BaseCurrency.Code,
                            BaseCurrency.Sign,
                            TargetCurrency.ID,
                            TargetCurrency.FullName,
                            TargetCurrency.Code,
                            TargetCurrency.Sign,
                            ExchangeRates.Rate
                        FROM ExchangeRates
                        JOIN Currencies AS BaseCurrency
                            ON ExchangeRates.BaseCurrencyId = BaseCurrency.ID
                        JOIN Currencies AS TargetCurrency
                            ON ExchangeRates.TargetCurrencyId = TargetCurrency.ID
                    """)
            exchange_rates = []
            for row in cursor.fetchall():
                exchange_rate = {
                    "id": row[0],
                    "baseCurrency": {
                        "id": row[1],
                        "name": row[2],
                        "code": row[3],
                        "sign": row[4]
                        },
                    "targetCurrency": {
                        "id": row[5],
                        "name": row[6],
                        "code": row[7],
                        "sign": row[8]
                        },
                    "rate": row[9]
                }
                exchange_rates.append(exchange_rate)
            response = json.dumps(exchange_rates, ensure_ascii=False)
            self.wfile.write(response.encode("utf-8"))
        except Exception:
            self.send_error(500, "Database is unavailable")

    elif self.path.startswith("/exchangeRate/"):
        name_pair = self.path.split("/")[-1]
        if len(name_pair) == 0:
            self.send_error(400, "Exchange rate codes are missing")
        else:
            if len(name_pair) == 6:
                base_code = name_pair[:3]
                target_code = name_pair[3:]
                cursor.execute("SELECT * FROM Currencies WHERE Code = ?",
                                (base_code,))
                base_cur = cursor.fetchone()

                cursor.execute("SELECT * FROM Currencies WHERE Code = ?",
                                (target_code,))
                target_cur = cursor.fetchone()

                if base_cur is None or target_cur is None:
                    self.send_error(404, "Exchange rate not found")
                    return

                try:
                    cursor.execute("""
                        SELECT
                            ExchangeRates.ID,
                            BaseCurrency.ID,
                            BaseCurrency.FullName,
                            BaseCurrency.Code,
                            BaseCurrency.Sign,
                            TargetCurrency.ID,
                            TargetCurrency.FullName,
                            TargetCurrency.Code,
                            TargetCurrency.Sign,
                            ExchangeRates.Rate
                        FROM ExchangeRates
                        JOIN Currencies AS BaseCurrency
                            ON ExchangeRates.BaseCurrencyId = BaseCurrency.ID
                        JOIN Currencies AS TargetCurrency
                            ON ExchangeRates.TargetCurrencyId = TargetCurrency.ID
                        WHERE BaseCurrency.Code = ? AND TargetCurrency.Code = ?
                    """, (base_code, target_code))

                    row = cursor.fetchone()
                    if row is None:
                        self.send_error(404, "Exchange rate not found")
                        return
                    exchange = {
                        "id": row[0],
                        "baseCurrency": {
                            "id": row[1],
                            "name": row[2],
                            "code": row[3],
                            "sign": row[4]
                            },
                        "targetCurrency": {
                            "id": row[5],
                            "name": row[6],
                            "code": row[7],
                            "sign": row[8]
                            },
                        "rate": row[9]
                    }
                    response = json.dumps(exchange, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(response.encode("utf-8"))
                except Exception:
                    self.send_error(500, "Database is unavailable")

            else:
                self.send_error(404, "Exchange rate not found")

    elif self.path.startswith("/exchange"):
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        if "from" not in params or "to" not in params or "amount" not in params:
            print("Отсутствует нужное поле формы")
            self.send_error(400, "Missing required form field")
            return

        curr_base = params["from"][0].strip()
        curr_target = params["to"][0].strip()
        amount = params["amount"][0].strip()

        if not curr_base or not curr_target or not amount:
            print("Отсутствует нужное поле формы")
            self.send_error(400, "Missing required form field")
            return

        if not curr_base.isalpha() or not curr_base.isupper() or not curr_target.isalpha() or not curr_target.isupper():
            print("Отсутствует нужное поле формы")
            self.send_error(400, "Missing required form field")
            return

        try:
            amount_value = float(amount)
            if amount_value <=0:
                print("Отсутствует нужное поле формы")
                self.send_error(400, "Missing required form field")
                return
        except ValueError:
            print("Отсутствует нужное поле формы")
            self.send_error(400, "Missing required form field")
            return

        try:
            cursor.execute("SELECT * FROM Currencies WHERE Code =?",
                        (curr_base,))
            curr_baseDB = cursor.fetchone()

            cursor.execute("SELECT * FROM Currencies WHERE Code = ?",
                        (curr_target,))
            curr_targetDB = cursor.fetchone()

            if curr_baseDB is None or curr_targetDB is None:
                print("Одна (или обе) валюта из валютной пары не существует в БД")
                self.send_error(404, "Currency not found")
                return

            cursor.execute("""
                SELECT
                    ExchangeRates.ID,
                    BaseCurrency.ID,
                    BaseCurrency.FullName,
                    BaseCurrency.Code,
                    BaseCurrency.Sign,
                    TargetCurrency.ID,
                    TargetCurrency.FullName,
                    TargetCurrency.Code,
                    TargetCurrency.Sign,
                    ExchangeRates.Rate
                FROM ExchangeRates
                JOIN Currencies AS BaseCurrency
                    ON ExchangeRates.BaseCurrencyId = BaseCurrency.ID
                JOIN Currencies AS TargetCurrency
                    ON ExchangeRates.TargetCurrencyId = TargetCurrency.ID
                WHERE BaseCurrency.Code = ? AND TargetCurrency.Code = ?
            """, (curr_base, curr_target))

            main_pair = cursor.fetchone()
            if main_pair:
                exchange = {
                    "baseCurrency": {
                        "id": main_pair[1],
                        "name": main_pair[2],
                        "code": main_pair[3],
                        "sign": main_pair[4]
                        },
                    "targetCurrency": {
                        "id": main_pair[5],
                        "name": main_pair[6],
                        "code": main_pair[7],
                        "sign": main_pair[8]
                        },
                    "rate": main_pair[9],
                    "amount": amount_value,
                    "convertedAmount": main_pair[9] * amount_value
                }
                response = json.dumps(exchange, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))
                return
        except Exception as error:
                print("Database error", error)
                self.send_error(500, "Database error")
                return


        try:
            cursor.execute("""
                SELECT
                    ExchangeRates.ID,
                    BaseCurrency.ID,
                    BaseCurrency.FullName,
                    BaseCurrency.Code,
                    BaseCurrency.Sign,
                    TargetCurrency.ID,
                    TargetCurrency.FullName,
                    TargetCurrency.Code,
                    TargetCurrency.Sign,
                    ExchangeRates.Rate
                FROM ExchangeRates
                JOIN Currencies AS BaseCurrency
                    ON ExchangeRates.BaseCurrencyId = BaseCurrency.ID
                JOIN Currencies AS TargetCurrency
                    ON ExchangeRates.TargetCurrencyId = TargetCurrency.ID
                WHERE BaseCurrency.Code = ? AND TargetCurrency.Code = ?
            """, (curr_target, curr_base))

            reverse_pair = cursor.fetchone()
            if reverse_pair[9] <= 0:
                print("Invalid exchange rate")
                self.send_error(400, "Invalid exchange rate")
                return

            if reverse_pair:
                exchange = {
                    "baseCurrency": {
                        "id": reverse_pair[5],
                        "name": reverse_pair[6],
                        "code": reverse_pair[7],
                        "sign": reverse_pair[8]
                        },
                    "targetCurrency": {
                        "id": reverse_pair[1],
                        "name": reverse_pair[2],
                        "code": reverse_pair[3],
                        "sign": reverse_pair[4]
                        },
                    "rate": 1/reverse_pair[9],
                    "amount": amount_value,
                    "convertedAmount": (1/reverse_pair[9]) * amount_value
                }
                response = json.dumps(exchange, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))
                return
        except Exception as error:
            print("Database error", error)
            self.send_error(500, "Database error")
            return


        try:
            cursor.execute("""
                SELECT
                    ExchangeRates.ID,
                    BaseCurrency.ID,
                    BaseCurrency.FullName,
                    BaseCurrency.Code,
                    BaseCurrency.Sign,
                    TargetCurrency.ID,
                    TargetCurrency.FullName,
                    TargetCurrency.Code,
                    TargetCurrency.Sign,
                    ExchangeRates.Rate
                FROM ExchangeRates
                JOIN Currencies AS BaseCurrency
                    ON ExchangeRates.BaseCurrencyId = BaseCurrency.ID
                JOIN Currencies AS TargetCurrency
                    ON ExchangeRates.TargetCurrencyId = TargetCurrency.ID
                WHERE BaseCurrency.Code = ? AND TargetCurrency.Code = ?
            """, ("USD", curr_base))

            usd_base_pair = cursor.fetchone()

            cursor.execute("""
                    SELECT
                        ExchangeRates.ID,
                        BaseCurrency.ID,
                        BaseCurrency.FullName,
                        BaseCurrency.Code,
                        BaseCurrency.Sign,
                        TargetCurrency.ID,
                        TargetCurrency.FullName,
                        TargetCurrency.Code,
                        TargetCurrency.Sign,
                        ExchangeRates.Rate
                    FROM ExchangeRates
                    JOIN Currencies AS BaseCurrency
                        ON ExchangeRates.BaseCurrencyId = BaseCurrency.ID
                    JOIN Currencies AS TargetCurrency
                        ON ExchangeRates.TargetCurrencyId = TargetCurrency.ID
                    WHERE BaseCurrency.Code = ? AND TargetCurrency.Code = ?
                """, ("USD", curr_target))

            usd_target_pair = cursor.fetchone()

            if usd_base_pair and usd_target_pair:
                usd_base_rate = usd_base_pair[9]
                usd_target_rate = usd_target_pair[9]

                if usd_base_rate <= 0 or usd_target_rate <= 0:
                    print("Invalid exchange rate")
                    self.send_error(400, "Invalid exchange rate")
                    return

                cross_rate = usd_target_rate / usd_base_rate

                exchange = {
                    "baseCurrency": {
                        "id": usd_base_pair[5],
                        "name": usd_base_pair[6],
                        "code": usd_base_pair[7],
                        "sign": usd_base_pair[8]
                        },
                    "targetCurrency": {
                        "id": usd_target_pair[5],
                        "name": usd_target_pair[6],
                        "code": usd_target_pair[7],
                        "sign": usd_target_pair[8]
                        },
                    "rate": cross_rate,
                    "amount": amount_value,
                    "convertedAmount": cross_rate * amount_value
                }
                response = json.dumps(exchange, ensure_ascii=False)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))
                return
        except Exception as error:
            print("Database error", error)
            self.send_error(500, "Database error")
            return
    else:
        self.send_error(404, "Not found")
