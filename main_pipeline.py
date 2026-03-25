"""
B2B Autonomous Pipeline Coordinator with Weighted Routing, Silent Logs, DaaS Engine & Dynamic Limits
"""
import logging
import time
import json
import os
import csv
import random
from datetime import datetime
from typing import Dict, Any, List
import requests

from dotenv import load_dotenv
from data_extractor import DataExtractor
from outreach_mailer import OutreachMailer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AgentCoordinator:
    def __init__(self, smtp_config: Dict[str, str], api_keys: Dict[str, str]) -> None:
        self.extractor = DataExtractor(timeout=15)
        self.mailer = OutreachMailer(
            smtp_server=smtp_config.get("server", ""),
            smtp_port=int(smtp_config.get("port", 587)),
            sender_email=smtp_config.get("email", ""),
            sender_password=smtp_config.get("password", "")
        )
        
        self.google_api_key = api_keys.get("google_places", "")
        self.tg_token = api_keys.get("telegram_token", "")
        self.tg_chat_id = api_keys.get("telegram_chat_id", "")
        
        self.state_file = "pipeline_state.json"
        self.failed_leads_file = "failed_leads.csv"
        self.contacted_file = "contacted_domains.txt" 
        self.offset = 0
        self.abort_current_cycle = False 
        
        self.target_pools = {
            "global": {
                "locations": [
                    "New York, USA", "London, UK", "Toronto, Canada", "Sydney, Australia",
                    "Dubai, UAE", "Singapore", "Berlin, Germany", "Amsterdam, Netherlands"
                ],
                "queries": [
                    "AI Automation Agency", "Data Science Consulting", "Machine Learning Startup",
                    "E-commerce Solutions", "B2B Lead Generation Agency", "Custom Software Development"
                ]
            },
            "russia": {
                "locations": [
                    "Moscow, Russia", "Saint Petersburg, Russia", "Kazan, Russia",
                    "Novosibirsk, Russia", "Yekaterinburg, Russia", "Sochi, Russia"
                ],
                "queries": [
                    "IT-консалтинг", "Разработка программного обеспечения", 
                    "Маркетинговое агентство", "Анализ данных", "Студия веб-дизайна"
                ]
            },
            "turkey": {
                "locations": [
                    "Istanbul, Turkey", "Izmir, Turkey", "Ankara, Turkey", "Antalya, Turkey", "Bursa, Turkey"
                ],
                "queries": [
                    "Yapay Zeka Çözümleri", "Veri Analizi Danışmanlık", "E-ticaret Yazılım",
                    "Dijital Pazarlama Ajansı", "Kurumsal Yazılım Geliştirme"
                ]
            }
        }
        
        self.is_override_active = False
        self.current_region = ""
        self.current_query = ""
        self.current_location = ""
        
        self._initialize_state()
        self._clear_pending_updates()
        self._send_telegram_message("🤖 <b>Enterprise Autonomous System INITIALIZED.</b>\nDynamic Limits & Template Rotation Active.\nType /help for commands.")

    def _clear_pending_updates(self) -> None:
        if not self.tg_token: return
        url = f"https://api.telegram.org/bot{self.tg_token}/getUpdates"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("result"):
                self.offset = data["result"][-1]["update_id"] + 1
                logging.info("Flushed old Telegram command queue.")
        except Exception:
            pass

    def _send_telegram_message(self, text: str) -> None:
        if not self.tg_token or not self.tg_chat_id: return
        url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
        payload = {"chat_id": self.tg_chat_id, "text": text, "parse_mode": "HTML"}
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception:
            pass

    def _is_contacted(self, domain: str) -> bool:
        if not os.path.exists(self.contacted_file) or not domain: 
            return False
        try:
            with open(self.contacted_file, 'r', encoding='utf-8') as f:
                return domain in f.read()
        except Exception:
            return False

    def _mark_contacted(self, domain: str) -> None:
        if not domain: return
        try:
            with open(self.contacted_file, 'a', encoding='utf-8') as f:
                f.write(domain + "\n")
        except Exception:
            pass

    def _log_premium_lead(self, company_name: str, domain: str, email: str, niche: str, region: str) -> None:
        filename = f"premium_leads_{region}.csv"
        file_exists = os.path.isfile(filename)
        try:
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Company Name", "Domain", "Email", "Niche", "Timestamp"])
                writer.writerow([company_name, domain, email, niche, time.strftime("%Y-%m-%d %H:%M:%S")])
        except Exception:
            pass

    def _select_autonomous_target(self) -> None:
        state = self._read_state()
        queued_reg = state.get("queued_region", "")
        locked_reg = state.get("locked_region", "")
        
        if locked_reg in self.target_pools:
            self.current_region = locked_reg
            logging.info("Locked region active: %s", self.current_region.upper())
        elif queued_reg in self.target_pools:
            self.current_region = queued_reg
            state["queued_region"] = "" 
            self._save_state(state)
            logging.info("Consumed queued reservation: %s", self.current_region.upper())
        else:
            regions = ["global", "russia", "turkey"]
            weights = [0.75, 0.20, 0.05]
            self.current_region = random.choices(regions, weights=weights, k=1)[0]
            
        region_data = self.target_pools[self.current_region]
        self.current_query = random.choice(region_data["queries"])
        self.current_location = random.choice(region_data["locations"])
        
        logging.info(
            "Autonomous target selected [%s]: %s in %s", 
            self.current_region.upper(), 
            self.current_query, 
            self.current_location
        )

    def _initialize_state(self) -> None:
        if not os.path.exists(self.state_file):
            self._select_autonomous_target()
            self._save_state({
                "date": datetime.now().strftime("%Y-%m-%d"), 
                "sent_count": 0,
                "daily_target": random.randint(42, 55), 
                "region": self.current_region,
                "query": self.current_query,
                "location": self.current_location,
                "total_sent_lifetime": 0,
                "location_stats": {},
                "queued_region": "",
                "locked_region": ""
            })
        else:
            state = self._read_state()
            self.current_region = state.get("region", "global")
            self.current_query = state.get("query")
            self.current_location = state.get("location")
            
            if "daily_target" not in state:
                state["daily_target"] = random.randint(42, 55)
            
            if not self.current_query or not self.current_location:
                self._select_autonomous_target()
                state = self._read_state() 
                state["region"] = self.current_region
                state["query"] = self.current_query
                state["location"] = self.current_location
                self._save_state(state)

    def _read_state(self) -> Dict[str, Any]:
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"date": datetime.now().strftime("%Y-%m-%d"), "sent_count": 0, "daily_target": 45}

    def _save_state(self, state: Dict[str, Any]) -> None:
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f)

    def verify_compliance_limits(self) -> bool:
        state = self._read_state()
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if state.get("date") != current_date:
            if not self.is_override_active:
                self._select_autonomous_target()
                logging.info(f"New Day Cycle Initiated: Target locked on {self.current_query} in {self.current_location}")
            
            state = self._read_state() 
            state["date"] = current_date
            state["sent_count"] = 0
            state["daily_target"] = random.randint(42, 55) # Her yeni günde zarı yeniden at
            state["region"] = self.current_region
            state["query"] = self.current_query
            state["location"] = self.current_location
            self._save_state(state)
            
        limit = state.get("daily_target", 45)
        return state.get("sent_count", 0) < limit

    def increment_counter(self) -> None:
        state = self._read_state()
        state["sent_count"] = state.get("sent_count", 0) + 1
        state["region"] = self.current_region
        state["query"] = self.current_query
        state["location"] = self.current_location
        
        state["total_sent_lifetime"] = state.get("total_sent_lifetime", 0) + 1
        loc_stats = state.get("location_stats", {})
        loc_stats[self.current_location] = loc_stats.get(self.current_location, 0) + 1
        state["location_stats"] = loc_stats
        
        self._save_state(state)

    def _log_failed_lead(self, company_name: str, domain: str) -> None:
        file_exists = os.path.isfile(self.failed_leads_file)
        try:
            with open(self.failed_leads_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_exists:
                    writer.writerow(["Company Name", "Domain", "Timestamp"])
                writer.writerow([company_name, domain, time.strftime("%Y-%m-%d %H:%M:%S")])
        except Exception:
            pass

    def _send_failed_leads_report(self) -> None:
        if not self.tg_token or not self.tg_chat_id or not os.path.isfile(self.failed_leads_file): return
        url = f"https://api.telegram.org/bot{self.tg_token}/sendDocument"
        try:
            with open(self.failed_leads_file, 'rb') as file:
                payload = {"chat_id": self.tg_chat_id, "caption": "📊 Failed Leads Report"}
                requests.post(url, data=payload, files={"document": file}, timeout=20)
            os.remove(self.failed_leads_file)
        except Exception:
            pass

    def _active_sleep(self, seconds: int) -> None:
        chunks = max(1, seconds // 5)
        for _ in range(chunks):
            if self.abort_current_cycle: break 
            self.poll_telegram_commands()
            time.sleep(5)

    def poll_telegram_commands(self) -> None:
        if not self.tg_token: return
        url = f"https://api.telegram.org/bot{self.tg_token}/getUpdates?offset={self.offset}&timeout=5"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            for result in data.get("result", []):
                self.offset = result["update_id"] + 1
                message = result.get("message", {}).get("text", "")
                
                if message == "/help":
                    self._send_telegram_message(
                        "🛠 <b>TELEMETRY COMMAND CENTER</b>\n\n"
                        "<b>/status</b> - Show daily metrics\n"
                        "<b>/report</b> - Show lifetime analytics\n"
                        "<b>/leads [region]</b> - Download Premium Data\n"
                        "<b>/failed</b> - Get failed leads CSV\n"
                        "<b>/now [region]</b> - INSTANT switch\n"
                        "<b>/always [region]</b> - LOCK to region\n"
                        "<b>/next [region]</b> - Queue next cycle\n"
                        "<b>/cancel</b> - Resume normal routing\n"
                        "<b>/help</b> - Show list"
                    )
                elif message == "/status":
                    state = self._read_state()
                    mode = "Manual Override" if self.is_override_active else "Autonomous Routing"
                    queued = state.get("queued_region", "")
                    locked = state.get("locked_region", "")
                    daily_target = state.get("daily_target", 45)
                    
                    queue_text = ""
                    if locked: queue_text = f"\nLocked Region: 🔒 {locked.upper()}"
                    elif queued: queue_text = f"\nQueued Next: 🗓️ {queued.upper()}"
                    
                    self._send_telegram_message(f"📡 <b>PIPELINE STATUS</b>\nMode: {mode}\nRegion: {self.current_region.upper()}\nTarget: {self.current_query} in {self.current_location}\nEmails Sent Today: {state.get('sent_count', 0)} / {daily_target}{queue_text}")
                
                elif message == "/report":
                    state = self._read_state()
                    total = state.get('total_sent_lifetime', 0)
                    loc_stats = state.get('location_stats', {})
                    
                    sorted_locs = sorted(loc_stats.items(), key=lambda x: x[1], reverse=True)[:10]
                    loc_str = "\n".join([f"📍 {loc}: {cnt} emails" for loc, cnt in sorted_locs])
                    if not loc_str:
                        loc_str = "No data gathered yet."
                        
                    self._send_telegram_message(
                        f"📈 <b>LIFETIME ANALYTICS REPORT</b>\n\n"
                        f"<b>Total Emails Sent:</b> {total}\n\n"
                        f"<b>Top Target Locations:</b>\n{loc_str}"
                    )
                
                elif message == "/failed":
                    if os.path.exists(self.failed_leads_file):
                        self._send_failed_leads_report()
                    else:
                        self._send_telegram_message("📁 <b>No Failed Leads.</b>\nThe list is currently empty.")

                elif message.startswith("/leads"):
                    parts = message.split()
                    if len(parts) >= 2:
                        req_region = parts[1].lower()
                        filename = f"premium_leads_{req_region}.csv"
                        if os.path.exists(filename):
                            doc_url = f"https://api.telegram.org/bot{self.tg_token}/sendDocument"
                            try:
                                with open(filename, 'rb') as file:
                                    payload = {"chat_id": self.tg_chat_id, "caption": f"💎 Premium DaaS Leads: {req_region.upper()}"}
                                    requests.post(doc_url, data=payload, files={"document": file}, timeout=20)
                            except Exception:
                                pass
                        else:
                            self._send_telegram_message(f"📁 <b>No leads yet for {req_region.upper()}.</b>")
                    else:
                        self._send_telegram_message("ℹ️ <b>Usage:</b> /leads [region]\nExample: /leads russia\nAvailable regions: global, russia, turkey")

                elif message.startswith("/always"):
                    parts = message.split()
                    if len(parts) >= 2:
                        req_region = parts[1].lower()
                        if req_region in self.target_pools:
                            state = self._read_state()
                            state["locked_region"] = req_region
                            state["queued_region"] = "" 
                            self._save_state(state)
                            self._send_telegram_message(f"🔒 <b>Region Locked!</b>\nBot will strictly target <b>{req_region.upper()}</b> from now on until canceled.")
                        else:
                            self._send_telegram_message(f"⚠️ <b>Invalid Region.</b>\nAvailable: {', '.join(self.target_pools.keys())}")
                
                elif message.startswith("/now"):
                    parts = message.split()
                    if len(parts) >= 2:
                        req_region = parts[1].lower()
                        if req_region in self.target_pools:
                            self.current_region = req_region
                            region_data = self.target_pools[self.current_region]
                            self.current_query = random.choice(region_data["queries"])
                            self.current_location = random.choice(region_data["locations"])
                            
                            state = self._read_state()
                            state["region"] = self.current_region
                            state["query"] = self.current_query
                            state["location"] = self.current_location
                            self._save_state(state)
                            
                            self.abort_current_cycle = True 
                            self._send_telegram_message(f"⚡ <b>Instant Switch Initiated!</b>\nAborting current cycle. Moving to <b>{req_region.upper()}</b> immediately.")
                        else:
                            self._send_telegram_message(f"⚠️ <b>Invalid Region.</b>\nAvailable: {', '.join(self.target_pools.keys())}")
                
                elif message.startswith("/next"):
                    parts = message.split()
                    if len(parts) >= 2:
                        req_region = parts[1].lower()
                        if req_region in self.target_pools:
                            state = self._read_state()
                            state["queued_region"] = req_region
                            self._save_state(state)
                            self._send_telegram_message(f"🗓️ <b>Queue Updated!</b>\nNext autonomous cycle is locked to: <b>{req_region.upper()}</b>")
                        else:
                            self._send_telegram_message(f"⚠️ <b>Invalid Region.</b>\nAvailable: {', '.join(self.target_pools.keys())}")
                
                elif message.startswith("/opportunity"):
                    parts = message.split('"')
                    if len(parts) >= 3:
                        self.current_query = parts[1]
                        self.current_location = parts[3] if len(parts) >= 5 else "Global"
                        self.current_region = "manual"
                        self.is_override_active = True
                        self._save_state(self._read_state())
                        self.abort_current_cycle = True 
                        self._send_telegram_message(f"🎯 <b>Manual Override Locked!</b>\nHunting for {self.current_query} in {self.current_location} immediately.")
                
                elif message == "/cancel":
                    self.is_override_active = False
                    state = self._read_state()
                    state["locked_region"] = ""
                    state["queued_region"] = ""
                    self._save_state(state)
                    self.abort_current_cycle = True 
                    self._send_telegram_message(f"🔄 <b>Overrides & Locks Canceled.</b>\nResumed weighted autonomous routing.")
        except Exception:
            pass

    def discover_leads(self, query: str, location: str) -> List[Dict[str, str]]:
        leads = []
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {"query": f"{query} in {location}", "key": self.google_api_key}
        
        try:
            response = requests.get(search_url, params=params, timeout=15)
            results = response.json().get("results", [])
            
            for place in results:
                self.poll_telegram_commands()
                if self.abort_current_cycle: break 
                
                place_id = place.get("place_id")
                company_name = place.get("name")
                if not place_id: continue
                    
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {"place_id": place_id, "fields": "website", "key": self.google_api_key}
                time.sleep(1.5)
                details_response = requests.get(details_url, params=details_params, timeout=15)
                website = details_response.json().get("result", {}).get("website")
                if website:
                    leads.append({
                        "company_name": company_name, 
                        "domain": website, 
                        "niche": query,
                        "region": self.current_region 
                    })
        except Exception as e:
            self._send_telegram_message(f"⚠️ <b>Discovery Error:</b> {str(e)}")
            
        return leads

    def daemon_loop(self) -> None:
        while True:
            try:
                self.abort_current_cycle = False 
                self.poll_telegram_commands()
                if not self.verify_compliance_limits():
                    self._active_sleep(3600)
                    continue
                
                raw_leads = self.discover_leads(self.current_query, self.current_location)
                if self.abort_current_cycle: 
                    continue 
                    
                if not raw_leads:
                    self._send_telegram_message(f"⚠️ <b>Warning:</b> Google API returned zero results for '{self.current_query}' in '{self.current_location}'. Cycling target.")
                    if not self.is_override_active:
                        self._select_autonomous_target()
                    self._active_sleep(1800)
                    continue
                
                failed_count = 0
                for lead in raw_leads:
                    self.poll_telegram_commands()
                    if self.abort_current_cycle: break 
                    if not self.verify_compliance_limits(): break
                        
                    domain = lead.get("domain")
                    company_name = lead.get("company_name", "Unknown")
                    
                    if self._is_contacted(domain):
                        logging.info("Skipping already contacted domain: %s", domain)
                        continue
                        
                    extracted_emails = self.extractor.process_target(domain)
                    
                    if extracted_emails:
                        lead["email"] = list(extracted_emails)[0]
                        dispatch_status = self.mailer.send_campaign([lead])
                        if dispatch_status:
                            self.increment_counter()
                            self._mark_contacted(domain) 
                            self._log_premium_lead(company_name, domain, lead["email"], lead["niche"], self.current_region)
                        self._active_sleep(180)
                    else:
                        self._log_failed_lead(company_name, domain)
                        failed_count += 1
                        self._active_sleep(5)
                
                if self.abort_current_cycle:
                    continue 
                
                if failed_count > 0:
                    logging.info(f"Logged {failed_count} failed leads to CSV. (Use /failed to retrieve)")
                    
                if not self.is_override_active:
                    self._select_autonomous_target()
                    
                self._active_sleep(1800)
                
            except Exception as e:
                self._send_telegram_message(f"🚨 <b>CRITICAL SYSTEM CRASH:</b>\n{str(e)}")
                self._active_sleep(60)

if __name__ == "__main__":
    load_dotenv()

    smtp_credentials = {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "port": os.getenv("SMTP_PORT", "587"),
        "email": os.getenv("SMTP_EMAIL", ""),
        "password": os.getenv("SMTP_PASSWORD", "")
    }
    external_apis = {
        "google_places": os.getenv("GOOGLE_PLACES_API_KEY", ""),
        "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
    }
    
    agent = AgentCoordinator(smtp_credentials, external_apis)
    agent.daemon_loop()