#Importer relevante biblioteker
import requests
import pickle
from bs4 import BeautifulSoup
import lxml
import pandas as pd
import csv
import sys
import json

print("script is running")

def check_smiley(postnummer_lower, postnummer_upper):
    
    errors = []

    # Header
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
    }
    
    # Sti til xml-fil fra Fødevarestyrelsen
    url = "https://www.foedevarestyrelsen.dk/_layouts/15/sdata/smiley_xml.xml"
  
    try:
        # Send request
        r = requests.get(url, headers=header,timeout=8)
        r.raise_for_status()
        
    except requests.exceptions.HTTPError as error:
        errors.append(error)       
    
    # Indlæs data
    xml = r.content.decode("utf-8-sig")
    soup = BeautifulSoup(xml, "xml")
    rows = soup.find_all("row")
    
    # Åbn tidligere data
    try:
        old_sur_smiley_liste = open('./csv/smileyer.csv', 'r')
        reader = csv.DictReader(old_sur_smiley_liste)
        old_sur_smiley_liste = list()
        
        for dictionary in reader:
            old_sur_smiley_liste.append(dictionary)

    # Hvis der ikke er data, opret tom liste
    except:
        old_sur_smiley_liste = []
            
    # Saml gamle cvrnumre, så man kan sammenholde med seneste data
    old_navnelbnr = []
    
    for hit in old_sur_smiley_liste:
        navnelbnr = hit["navnelbnr"]
        old_navnelbnr.append(navnelbnr)
            
    # Er der ændringer, bliver denne værdi True
    changes_found = False
    
    # Tom liste, hvor man lægger nye dicts
    sur_smiley_liste = []
    
    try:
    # Loop gennem data for at finde sure smileys og postnumre
        for row in rows:
            seneste_kontrol_tag = row.find("seneste_kontrol")
            seneste_kontrol = seneste_kontrol_tag.get_text()
            
            postnr_tag = row.find("postnr")
            postnr = int(postnr_tag.get_text())
        
            # Hvis der findes sure smileys blandt fynske virksomheder, så fortsæt
            if seneste_kontrol == "4" and postnr > postnummer_lower and postnr < postnummer_upper:
                cvr_tag = row.find("cvrnr")
                cvr = cvr_tag.get_text()
        
                pnr_tag = row.find("pnr")
                pnr = pnr_tag.get_text()
        
                navn_tag = row.find("navn1")
                navn = navn_tag.get_text()
        
                url_tag = row.find("URL")
                url = url_tag.get_text()
        
                adresse_tag = row.find("adresse1")
                adresse = adresse_tag.get_text()
                
                by_tag = row.find("By")
                by = by_tag.get_text()
                
                navnelbnr_tag = row.find("navnelbnr")
                navnelbnr = navnelbnr_tag.get_text()        
        
                kontrol_dato_tag = row.find("seneste_kontrol_dato")
                kontrol_dato_str = kontrol_dato_tag.get_text()
             
                smiley_dict = {
                    "cvrnr": cvr,
                    "pnr": pnr,
                    "navn": navn,
                    "seneste_kontrol": seneste_kontrol,
                    "kontrol_dato_str": kontrol_dato_str,
                    "navnelbnr": navnelbnr,
                    "url": url,
                    "adresse": adresse,
                    "postnr": postnr,
                    "by": by
                }
        
                # Tilføj dict til listen over sure smileyer på Fyn
                sur_smiley_liste.append(smiley_dict)
    except:
        errors.append({"message":"Iteration was not succesful.",
                       "error": sys.exc_info()})
                
    # opret liste for at kunne sammneholde med gamle data           
    new_navnelbnr = []
    ny_sur_smiley_liste = []
    ikke_sur_smiley_liste = []
    
    # Loop gennem seneste data og saml cvrnumre
    for hit in sur_smiley_liste:
        navnelbnr = hit["navnelbnr"]
        new_navnelbnr.append(navnelbnr)
    
        # Hvis et navnelbnr ikke er i de gamle data, så raise flag og tilføj til ny liste
        if navnelbnr not in old_navnelbnr:
            ny_smiley_dict = {
                "cvrnr": hit["cvrnr"],
                "pnr": hit["pnr"],
                "navn": hit["navn"],
                "seneste_kontrol": hit["seneste_kontrol"],
                "kontrol_dato_str": hit["kontrol_dato_str"],
                "navnelbnr": hit["navnelbnr"],
                "url": hit["url"],
                "adresse": hit["adresse"],
                "postnr": hit["postnr"],
                "by": hit["by"]
            }
            
            ny_sur_smiley_liste.append(ny_smiley_dict)
            changes_found = True

            
    for hit in old_sur_smiley_liste:
        navnelbnr = hit["navnelbnr"]
    
        # Hvis et cvrnummer ikke længere er blandt virksomheder med sure smileys.
        if navnelbnr not in new_navnelbnr:
            ikke_sur_smiley_dict = {
                "cvrnr": hit["cvrnr"],
                "pnr": hit["pnr"],
                "navn": hit["navn"],
                "seneste_kontrol": "1-3",
                "kontrol_dato_str": hit["kontrol_dato_str"],
                "navnelbnr": hit["navnelbnr"],
                "url": hit["url"],
                "adresse": hit["adresse"],
                "postnr": hit["postnr"],
                "by": hit["by"]
            }
     
            
            ikke_sur_smiley_liste.append(ikke_sur_smiley_dict)
            changes_found = True
    
    # Hvis der er nye virksomheder, så overskriv den gamle fil. 

    if changes_found is True:
        a = pd.DataFrame(sur_smiley_liste)
        a.to_csv('./csv/smileyer.csv')
        print("Added csv-file, because changes were found")

    b = pd.DataFrame(ny_sur_smiley_liste)
    b.to_csv("./csv/nye-sure-smileyer.csv")
    print("added new smiley reports")

    c = pd.DataFrame(ikke_sur_smiley_liste)
    c.to_csv("csv/ikke-sure-smileyer.csv")
    print(c)
    print("added ikke-sure-smileyer.csv")

    to_return = {
        "data": {
            "ny_sur_smiley_liste": ny_sur_smiley_liste,
            "ikke_sur_smiley_liste": ikke_sur_smiley_liste,
            "komplet_liste": sur_smiley_liste,
            "source": "Fødevarestyrelsen, URL: https://www.foedevarestyrelsen.dk/_layouts/15/sdata/smiley_xml.xml"
            },
        "errors": errors
}

c = pd.DataFrame("ikke_sur_smiley_liste")
c.to_csv("csv/ikke-sure-smileyer.csv")
        
# check_smiley(4999,5999)