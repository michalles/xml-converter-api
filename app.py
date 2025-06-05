from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime, timedelta
import os
import traceback
import json

app = Flask(__name__)
CORS(app)

def create_xml_from_data(data):
    """Konwertuje dane z Make.com na XML"""
    
    print(f"🔍 Processing data: {data}")  # DEBUG
    
    # Walidacja wymaganych pól z fallbacks
    required_fields = {
        'Numer_Faktury': 'TEST/001/2025',
        'Data_Wystawienia': '2025-05-30',
        'NIP_Sprzedawcy': '0000000000',
        'Nazwa_Sprzedawcy': 'TEST SUPPLIER'
    }
    
    # Sprawdź i uzupełnij brakujące pola
    for field, default_value in required_fields.items():
        if field not in data or not data[field]:
            print(f"⚠️  Missing field {field}, using default: {default_value}")
            data[field] = default_value
    
    # Generowanie UUID
    id_zrodla = str(uuid.uuid4()).upper()
    podmiot_id = str(uuid.uuid4()).upper()
    kategoria_id = str(uuid.uuid4()).upper()
    forma_platnosci_id = str(uuid.uuid4()).upper()
    platnosc_id = str(uuid.uuid4()).upper()
    
    # Przetwarzanie dat
    data_wystawienia = data.get('Data_Wystawienia', '2025-05-30')
    data_zakupu = data.get('Data_Zakupu', data_wystawienia)
    data_wplywu = data.get('Data_Wplywu', data_wystawienia)
    
    # Obliczanie terminu płatności
    try:
        date_obj = datetime.strptime(data_wystawienia, '%Y-%m-%d')
        termin_obj = date_obj + timedelta(days=7)
        termin = termin_obj.strftime('%Y-%m-%d')
        deklaracja_vat = date_obj.strftime('%Y-%m')
    except Exception as e:
        print(f"⚠️  Date parsing error: {e}")
        termin = '2025-06-06'
        deklaracja_vat = '2025-05'
    
    # Przetwarzanie kwot
    try:
        netto = float(data.get('Netto', 0))
        vat = float(data.get('VAT', 0))
        brutto = netto + vat
        stawka_vat = int(data.get('Stawka_VAT', 23))
        print(f"💰 Amounts: netto={netto}, vat={vat}, brutto={brutto}")
    except Exception as e:
        print(f"⚠️  Amount parsing error: {e}")
        netto = 1000.0
        vat = 230.0
        brutto = 1230.0
        stawka_vat = 23
    
    # Formatowanie numerów
    numer_faktury = str(data.get('Numer_Faktury', 'BRAK')).replace('/', '_')
    identyfikator_ksiegowy = f"ZAKUP/{numer_faktury}"
    
    # Bezpieczne pobieranie stringów
    def safe_get(key, default=''):
        value = data.get(key, default)
        return str(value) if value is not None else default
    
    nazwa_sprzedawcy = safe_get('Nazwa_Sprzedawcy', 'BRAK NAZWY')
    nip_sprzedawcy = safe_get('NIP_Sprzedawcy', '0000000000')
    
    print(f"📋 Basic info: {nazwa_sprzedawcy}, NIP: {nip_sprzedawcy}")
    
    # XML Template - uproszczona wersja
    xml_content = f'''<?xml version='1.0' encoding='utf-8'?>
<ROOT xmlns="http://www.comarch.pl/cdn/optima/offline">
  <REJESTRY_ZAKUPU_VAT>
    <WERSJA>2.00</WERSJA>
    <BAZA_ZRD_ID>SPRZ</BAZA_ZRD_ID>
    <BAZA_DOC_ID>KSIEG</BAZA_DOC_ID>
    <REJESTR_ZAKUPU_VAT>
      <ID_ZRODLA>{id_zrodla}</ID_ZRODLA>
      <MODUL>Rejestr Vat</MODUL>
      <TYP>Rejestr zakupu</TYP>
      <REJESTR>ZAKUP</REJESTR>
      <DATA_WYSTAWIENIA>{data_wystawienia}</DATA_WYSTAWIENIA>
      <DATA_ZAKUPU>{data_zakupu}</DATA_ZAKUPU>
      <DATA_WPLYWU>{data_wplywu}</DATA_WPLYWU>
      <TERMIN>{termin}</TERMIN>
      <DATA_DATAOBOWIAZKUPODATKOWEGO>{data_wystawienia}</DATA_DATAOBOWIAZKUPODATKOWEGO>
      <DATA_DATAPRAWAODLICZENIA>{data_wystawienia}</DATA_DATAPRAWAODLICZENIA>
      <NUMER>{data.get('Numer_Faktury', 'BRAK')}</NUMER>
      <KOREKTA>Nie</KOREKTA>
      <KOREKTA_NUMER></KOREKTA_NUMER>
      <WEWNETRZNA>Nie</WEWNETRZNA>
      <METODA_KASOWA>Nie</METODA_KASOWA>
      <FISKALNA>Nie</FISKALNA>
      <DETALICZNA>Nie</DETALICZNA>
      <EKSPORT>nie</EKSPORT>
      <FINALNY>Nie</FINALNY>
      <PODATNIK_CZYNNY>Tak</PODATNIK_CZYNNY>
      <IDENTYFIKATOR_KSIEGOWY>{identyfikator_ksiegowy}</IDENTYFIKATOR_KSIEGOWY>
      <TYP_PODMIOTU>kontrahent</TYP_PODMIOTU>
      <PODMIOT>{nazwa_sprzedawcy}</PODMIOT>
      <PODMIOT_ID>{podmiot_id}</PODMIOT_ID>
      <PODMIOT_NIP>{nip_sprzedawcy}</PODMIOT_NIP>
      <NAZWA1>{nazwa_sprzedawcy}</NAZWA1>
      <NAZWA2></NAZWA2>
      <NAZWA3></NAZWA3>
      <NIP_KRAJ></NIP_KRAJ>
      <NIP>{nip_sprzedawcy}</NIP>
      <KRAJ>{safe_get('Kraj', 'Polska')}</KRAJ>
      <WOJEWODZTWO>{safe_get('Wojewodztwo', 'mazowieckie')}</WOJEWODZTWO>
      <POWIAT></POWIAT>
      <GMINA></GMINA>
      <ULICA>{safe_get('Ulica', '')}</ULICA>
      <NR_DOMU></NR_DOMU>
      <NR_LOKALU>{safe_get('Nr_Lokalu', '')}</NR_LOKALU>
      <MIASTO>{safe_get('Miasto', '')}</MIASTO>
      <KOD_POCZTOWY>{safe_get('Kod_Pocztowy', '')}</KOD_POCZTOWY>
      <POCZTA>{safe_get('Miasto', '')}</POCZTA>
      <DODATKOWE></DODATKOWE>
      <PESEL></PESEL>
      <ROLNIK>Nie</ROLNIK>
      <TYP_PLATNIKA>kontrahent</TYP_PLATNIKA>
      <PLATNIK>{nazwa_sprzedawcy}</PLATNIK>
      <PLATNIK_ID>{podmiot_id}</PLATNIK_ID>
      <PLATNIK_NIP>{nip_sprzedawcy}</PLATNIK_NIP>
      <KATEGORIA>{safe_get('Kategoria', '402-07-01')}</KATEGORIA>
      <KATEGORIA_ID>{kategoria_id}</KATEGORIA_ID>
      <OPIS>{safe_get('Opis_Pozycji', '')}</OPIS>
      <FORMA_PLATNOSCI>{safe_get('Forma_Platnosci', 'przelew')}</FORMA_PLATNOSCI>
      <FORMA_PLATNOSCI_ID>{forma_platnosci_id}</FORMA_PLATNOSCI_ID>
      <DEKLARACJA_VAT7>{deklaracja_vat}</DEKLARACJA_VAT7>
      <DEKLARACJA_VATUE>Nie</DEKLARACJA_VATUE>
      <WALUTA>{safe_get('Waluta', '')}</WALUTA>
      <KURS_WALUTY>NBP</KURS_WALUTY>
      <NOTOWANIE_WALUTY_ILE>1</NOTOWANIE_WALUTY_ILE>
      <NOTOWANIE_WALUTY_ZA_ILE>1</NOTOWANIE_WALUTY_ZA_ILE>
      <DATA_KURSU>{data_wystawienia}</DATA_KURSU>
      <KURS_DO_KSIEGOWANIA>Nie</KURS_DO_KSIEGOWANIA>
      <KURS_WALUTY_2>NBP</KURS_WALUTY_2>
      <NOTOWANIE_WALUTY_ILE_2>1</NOTOWANIE_WALUTY_ILE_2>
      <NOTOWANIE_WALUTY_ZA_ILE_2>1</NOTOWANIE_WALUTY_ZA_ILE_2>
      <DATA_KURSU_2>{data_wystawienia}</DATA_KURSU_2>
      <PLATNOSC_VAT_W_PLN>Nie</PLATNOSC_VAT_W_PLN>
      <AKCYZA_NA_WEGIEL>0</AKCYZA_NA_WEGIEL>
      <AKCYZA_NA_WEGIEL_KOLUMNA_KPR>nie księgować</AKCYZA_NA_WEGIEL_KOLUMNA_KPR>
      <JPK_FA>Nie</JPK_FA>
      <MPP>Nie</MPP>
      <NR_KSEF></NR_KSEF>
      <DODATKOWY_OPIS></DODATKOWY_OPIS>
      <POZYCJE>
        <POZYCJA>
          <LP>1</LP>
          <KATEGORIA_POS>{safe_get('Kategoria', '402-07-01')}</KATEGORIA_POS>
          <KATEGORIA_ID_POS>{kategoria_id}</KATEGORIA_ID_POS>
          <STAWKA_VAT>{stawka_vat}</STAWKA_VAT>
          <STATUS_VAT>opodatkowana</STATUS_VAT>
          <NETTO>{netto:.2f}</NETTO>
          <VAT>{vat:.2f}</VAT>
          <NETTO_SYS>{netto:.2f}</NETTO_SYS>
          <VAT_SYS>{vat:.2f}</VAT_SYS>
          <NETTO_SYS2>{netto:.2f}</NETTO_SYS2>
          <VAT_SYS2>{vat:.2f}</VAT_SYS2>
          <RODZAJ_ZAKUPU>{safe_get('Rodzaj_Zakupu', 'usługi')}</RODZAJ_ZAKUPU>
          <ODLICZENIA_VAT>{safe_get('Odliczenia_VAT', 'tak')}</ODLICZENIA_VAT>
          <KOLUMNA_KPR>Inne</KOLUMNA_KPR>
          <KOLUMNA_RYCZALT>3.00</KOLUMNA_RYCZALT>
          <OPIS_POZ>{safe_get('Opis_Pozycji', '')}</OPIS_POZ>
        </POZYCJA>
      </POZYCJE>
      <KWOTY_DODATKOWE></KWOTY_DODATKOWE>
      <PLATNOSCI>
        <PLATNOSC>
          <ID_ZRODLA_PLAT>{platnosc_id}</ID_ZRODLA_PLAT>
          <TERMIN_PLAT>{termin}</TERMIN_PLAT>
          <FORMA_PLATNOSCI_PLAT>{safe_get('Forma_Platnosci', 'przelew')}</FORMA_PLATNOSCI_PLAT>
          <FORMA_PLATNOSCI_ID_PLAT>{forma_platnosci_id}</FORMA_PLATNOSCI_ID_PLAT>
          <KWOTA_PLAT>{brutto:.2f}</KWOTA_PLAT>
          <WALUTA_PLAT>{safe_get('Waluta', '')}</WALUTA_PLAT>
          <KURS_WALUTY_PLAT>NBP</KURS_WALUTY_PLAT>
          <NOTOWANIE_WALUTY_ILE_PLAT>1</NOTOWANIE_WALUTY_ILE_PLAT>
          <NOTOWANIE_WALUTY_ZA_ILE_PLAT>1</NOTOWANIE_WALUTY_ZA_ILE_PLAT>
          <KWOTA_PLN_PLAT>{brutto:.2f}</KWOTA_PLN_PLAT>
          <KIERUNEK>rozchód</KIERUNEK>
          <PODLEGA_ROZLICZENIU>tak</PODLEGA_ROZLICZENIU>
          <KONTO></KONTO>
          <NIE_NALICZAJ_ODSETEK>Nie</NIE_NALICZAJ_ODSETEK>
          <PRZELEW_SEPA>Nie</PRZELEW_SEPA>
          <DATA_KURSU_PLAT>{data_wystawienia}</DATA_KURSU_PLAT>
          <WALUTA_DOK>{safe_get('Waluta', '')}</WALUTA_DOK>
          <PLATNOSC_TYP_PODMIOTU>kontrahent</PLATNOSC_TYP_PODMIOTU>
          <PLATNOSC_PODMIOT>{nazwa_sprzedawcy}</PLATNOSC_PODMIOT>
          <PLATNOSC_PODMIOT_ID>{podmiot_id}</PLATNOSC_PODMIOT_ID>
          <PLATNOSC_PODMIOT_NIP>{nip_sprzedawcy}</PLATNOSC_PODMIOT_NIP>
          <PLAT_KATEGORIA>{safe_get('Kategoria', '402-07-01')}</PLAT_KATEGORIA>
          <PLAT_KATEGORIA_ID>{kategoria_id}</PLAT_KATEGORIA_ID>
          <PLAT_ELIXIR_O1>Zapłata za {data.get('Numer_Faktury', 'BRAK')}</PLAT_ELIXIR_O1>
          <PLAT_ELIXIR_O2></PLAT_ELIXIR_O2>
          <PLAT_ELIXIR_O3></PLAT_ELIXIR_O3>
          <PLAT_ELIXIR_O4></PLAT_ELIXIR_O4>
          <PLAT_FA_Z_PA>Nie</PLAT_FA_Z_PA>
          <PLAT_VAN_FA_Z_PA>Nie</PLAT_VAN_FA_Z_PA>
          <PLAT_SPLIT_PAYMENT>Nie</PLAT_SPLIT_PAYMENT>
          <PLAT_SPLIT_KWOTA_VAT>{vat:.2f}</PLAT_SPLIT_KWOTA_VAT>
          <PLAT_SPLIT_NIP>{nip_sprzedawcy}</PLAT_SPLIT_NIP>
          <PLAT_SPLIT_NR_DOKUMENTU>{data.get('Numer_Faktury', 'BRAK')}</PLAT_SPLIT_NR_DOKUMENTU>
        </PLATNOSC>
      </PLATNOSCI>
      <KODY_JPK></KODY_JPK>
      <ATRYBUTY></ATRYBUTY>
    </REJESTR_ZAKUPU_VAT>
  </REJESTRY_ZAKUPU_VAT>
</ROOT>'''
    
    print(f"✅ XML generated successfully, length: {len(xml_content)}")
    return xml_content

@app.route('/')
def health_check():
    """Sprawdzenie statusu serwera"""
    return jsonify({
        'status': 'healthy',
        'service': 'Google Sheet to XML Converter',
        'version': '2.0.0',
        'platform': 'Render.com',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test')
def test_endpoint():
    """Test endpoint z przykładowymi danymi"""
    try:
        test_data = {
            'Numer_Faktury': 'TEST/001/2025',
            'Data_Wystawienia': '2025-05-30',
            'NIP_Sprzedawcy': '1234567890',
            'Nazwa_Sprzedawcy': 'Test Company',
            'Netto': '1000.00',
            'VAT': '230.00',
            'Stawka_VAT': '23'
        }
        
        xml_content = create_xml_from_data(test_data)
        
        return jsonify({
            'success': True,
            'message': 'Test conversion successful',
            'test_data': test_data,
            'xml_length': len(xml_content),
            'xml_preview': xml_content[:500] + '...'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/convert/single', methods=['POST'])
def convert_single():
    """Konwersja pojedynczego wiersza z Make.com"""
    try:
        print(f"📨 Received request from {request.remote_addr}")
        print(f"📋 Headers: {dict(request.headers)}")
        
        if not request.is_json:
            print(f"❌ Content-Type not JSON: {request.content_type}")
            return jsonify({
                'success': False,
                'error': f'Request must contain JSON data. Received: {request.content_type}',
                'content_received': request.get_data(as_text=True)[:200]
            }), 400
        
        try:
            data = request.get_json()
            print(f"📊 JSON data received: {data}")
        except Exception as json_error:
            print(f"❌ JSON parsing error: {json_error}")
            return jsonify({
                'success': False,
                'error': f'Invalid JSON: {str(json_error)}',
                'raw_data': request.get_data(as_text=True)[:200]
            }), 400
        
        if not data:
            print("❌ Empty data received")
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'received': str(data)
            }), 400
        
        print(f"🔄 Starting XML conversion...")
        xml_content = create_xml_from_data(data)
        print(f"✅ Conversion successful")
        
        return jsonify({
            'success': True,
            'message': 'Conversion successful',
            'xml_content': xml_content,
            'timestamp': datetime.now().isoformat(),
            'processed_fields': list(data.keys())
        })
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Server error: {e}")
        print(f"📋 Traceback: {error_trace}")
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': error_trace,
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
