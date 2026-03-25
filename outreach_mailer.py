"""
B2B Outreach Automation - Ultra Casual "Human" Templates with Hybrid Signature
"""
import smtplib
import logging
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OutreachMailer:
    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str, sender_password: str) -> None:
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def _build_payload(self, target_email: str, company_name: str, niche: str, region: str = "global") -> MIMEMultipart:
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = target_email

        if region == "russia":
            subjects = [
                f"Вопрос по данным для {company_name}",
                f"Парсинг и боты для {company_name}"
            ]
            bodies = [
                (
                    f"Привет, команда {company_name}!\n\n"
                    f"Я независимый Python-разработчик. Изучал вашу работу в нише {niche} и заметил, что вам, возможно, приходится собирать много данных вручную.\n\n"
                    "Я пишу кастомных ботов для парсинга и собираю готовые B2B базы (Excel/CSV), чтобы избавить команды от этой рутины. "
                    "Вы сейчас делегируете кому-то сбор данных или лидогенерацию?\n\n"
                    "Дайте знать, если интересно пообщаться.\n\n"
                    "Берк\nPython Developer\ngithub.com/berk-io\nlinkedin.com/in/berk-kurtcu"
                ),
                (
                    f"Здравствуйте!\n\n"
                    f"Меня зовут Берк, я пишу скрипты на Python для автоматизации бизнес-процессов. "
                    f"Наткнулся на {company_name} и решил написать.\n\n"
                    "Если вам когда-нибудь понадобятся готовые базы клиентов для рассылок или бот, который будет собирать данные с сайтов 24/7 — буду рад помочь. "
                    "Интересно ли вам взглянуть на примеры моих работ?\n\n"
                    "Хорошего дня,\nБерк\ngithub.com/berk-io\nlinkedin.com/in/berk-kurtcu"
                )
            ]
            msg['Subject'] = random.choice(subjects)
            body = random.choice(bodies)

        elif region == "turkey":
            subjects = [
                f"{company_name} veri toplama işleri",
                f"Selam {company_name} ekibi - Python botları"
            ]
            bodies = [
                (
                    f"Selam {company_name} ekibi,\n\n"
                    f"Ben serbest çalışan bir Python geliştiricisiyim. İnternette {niche} tarafındaki işlerinize denk geldim.\n\n"
                    "B2B müşteri listeleri çıkarmak veya rakip analizi için veri toplamak genelde çok vakit alıyor. Ben şirketlere özel veri çekme botları yazıyorum, bazen de hazır Excel müşteri listeleri sağlıyorum. "
                    "Şu sıralar bu tarz amelelik gerektiren veri işlerini otomatize etme gibi bir düşünceniz var mı?\n\n"
                    "İlgilenirseniz Github'daki projelerimi atabilirim.\n\n"
                    "Görüşmek üzere,\nBerk\nPython Developer\ngithub.com/berk-io\nlinkedin.com/in/berk-kurtcu"
                ),
                (
                    f"Merhaba,\n\n"
                    f"İsmim Berk, veri madenciliği ve otomasyon botları yazan bir yazılımcıyım. {company_name} olarak sektördeki çalışmalarınız dikkatimi çekti.\n\n"
                    "Eğer manuel veri girişiyle uğraşmak yerine arka planda sizin için 7/24 çalışacak bir bota ihtiyacınız olursa veya direkt sektörel B2B iletişim listeleri satın almak isterseniz bana ulaşabilirsiniz.\n\n"
                    "İyi çalışmalar dilerim,\nBerk\ngithub.com/berk-io\nlinkedin.com/in/berk-kurtcu"
                )
            ]
            msg['Subject'] = random.choice(subjects)
            body = random.choice(bodies)

        else: # Default: Global (English)
            subjects = [
                f"Quick question about {company_name} data",
                f"Custom data scrapers for {company_name}"
            ]
            bodies = [
                (
                    f"Hey {company_name} team,\n\n"
                    f"I'm a freelance Python developer. I was looking at your work in the {niche} space and realized you guys might be handling a lot of data collection manually.\n\n"
                    "I build custom web scrapers and provide ready-to-use B2B lead lists (Excel) so teams don't have to waste time on manual data entry. "
                    "Are you currently outsourcing any of your data collection tasks?\n\n"
                    "Let me know if you'd be open to a quick chat or want to see some of my work.\n\n"
                    "Cheers,\nBerk\nPython Developer\ngithub.com/berk-io\nlinkedin.com/in/berk-kurtcu"
                ),
                (
                    f"Hi there,\n\n"
                    f"My name is Berk and I write Python automation scripts. I came across {company_name} and wanted to reach out.\n\n"
                    "If you guys ever need a custom bot to scrape web data 24/7, or just need pre-verified B2B lead lists for your campaigns, that's exactly what I do. "
                    "Would you be interested in seeing a quick sample of my recent projects?\n\n"
                    "Best,\nBerk\ngithub.com/berk-io\nlinkedin.com/in/berk-kurtcu"
                )
            ]
            msg['Subject'] = random.choice(subjects)
            body = random.choice(bodies)

        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        return msg

    def send_campaign(self, leads: List[Dict[str, str]], daily_limit: int = 50) -> bool:
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            for lead in leads:
                target_email = lead.get("email")
                company_name = lead.get("company_name")
                niche = lead.get("niche", "tech")
                region = lead.get("region", "global") 
                
                if not target_email or not company_name:
                    continue
                    
                msg = self._build_payload(target_email, company_name, niche, region)
                server.send_message(msg)
                logging.info("Localized DaaS outreach (%s) delivered to %s", region.upper(), target_email)
                
            server.quit()
            return True
            
        except Exception as e:
            logging.error("SMTP Error: %s", str(e))
            return False