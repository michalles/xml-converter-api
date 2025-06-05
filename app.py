from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from datetime import datetime, timedelta
import traceback
import html

app = Flask(__name__)
CORS(app)

def convert_excel_date(excel_date):
    """Convert Excel serial date to YYYY-MM-DD format"""
    try:
        # If it's already a string in correct format, return as is
        if isinstance(excel_date, str) and len(excel_date) == 10 and '-' in excel_date:
            return excel_date
        
        # Convert to float for calculation
        excel_date = float(excel_date)
        
        # Excel epoch starts at 1900-01-01, but Excel incorrectly treats 1900 as leap year
        # So we need to subtract 1 day for dates after Feb 28, 1900
        if excel_date > 59:  # After Feb 28, 1900
            excel_date -= 1
            
        # Calculate the date
        epoch = datetime(1899, 12, 30)  # Excel's actual epoch
        converted_date = epoch + timedelta(days=excel_date)
        
        return converted_date.strftime('%Y-%m-%d')
        
    except (ValueError, TypeError):
        # If conversion fails, return current date
        return datetime.now().strftime('%Y-%m-%d')

def escape_xml(text):
    """Escape special characters for XML"""
    if not text:
        return ""
    # Convert to string if not already
    text = str(text)
    # Escape XML special characters
    text = html.escape(text, quote=False)
    return text

def create_xml(data):
    try:
        # Generate unique IDs
        id_zrodla = str(uuid.uuid4()).upper()
        platnosc_id = str(uuid.uuid4()).upper()
        
        # Podstawowe pola z konwersją dat - MAPOWANIE INDEKSÓW
        numer_faktury = data.get('0', data.get('A', 'BRAK'))  # Kolumna A
        data_wystawienia = convert_excel_date(data.get('1', data.get('B', '2025-01-01')))  # Kolumna B
        data_zakupu = convert_excel_date(data.get('2', data.get('C', data_wystawienia)))  # Kolumna C
        data_wplywu = convert_excel_date(data.get('3', data.get('D', data_wystawienia)))  # Kolumna D
        termin_platnosci = convert_excel_date(data.get('4', data.get('E', '2025-01-01')))  # Kolumna E
        
        # Dane sprzedawcy - z escapowaniem znaków XML
        nip_sprzedawcy = data.get('5', data.get('F', '0000000000'))  # Kolumna F
        nazwa_sprzedawcy = escape_xml(data.get('6', data.get('G', 'BRAK')))  # Kolumna G
        ulica = escape_xml(data.get('7', data.get('H', '')))  # Kolumna H
        kod_pocztowy = data.get('10', data.get('J', ''))  # Kolumna J (uwaga: 8=I, 9=?, 10=J)
        miasto = escape_xml(data.get('9', data.get('I', '')))  # Kolumna I
        kraj = escape_xml(data.get('11', data.get('K', 'Polska')))  # Kolumna K
        
        # Kwoty
        stawka_vat = float(data.get('12', data.get('L', 23)))  # Kolumna L
        netto = float(data.get('13', data.get('M', 0)))  # Kolumna M
        vat = float(data.get('14', data.get('N', 0)))  # Kolumna N
        brutto = float(data.get('15', data.get('O', netto + vat)))  # Kolumna O
        waluta = data.get('16', data.get('P', 'PLN'))  # Kolumna P
        forma_platnosci = escape_xml(data.get('17', data.get('Q', '')))  # Kolumna Q
        
        # Identyfikator księgowy - escapowanie
        numer_clean = escape_xml(numer_faktury).replace('/', '_')
        identyfikator_ksiegowy = f"ZAKUP/{numer_clean}"
        
        # XML Template - POPRAWIONE IDENTYFIKATORY
        xml_content = f'''<?xml version='1.0' encoding='utf-8'?>
<ROOT xmlns="http://www.comarch.pl/cdn/optima/offline">
  <REJESTRY_ZAKUPU_VAT>
    <WERSJA>2.00</WERSJA>
    <BAZA_ZRD_ID>KSIEG</BAZA_ZRD_ID>
    <BAZA_DOC_ID>KSIEG</BAZA_DOC_ID>
    <REJESTR_ZAKUPU_VAT>
      <ID_ZRODLA>{id_zrodla}</ID_ZRODLA>
      <MODUL>Rejestr Vat</MODUL>
      <TYP>Rejestr zakupu</TYP>
      <REJESTR>ZAKUP</REJESTR>
      <DATA_WYSTAWIENIA>{data_wystawienia}</DATA_WYSTAWIENIA>
      <DATA_ZAKUPU>{data_zakupu}</DATA_ZAKUPU>
      <DATA_WPLYWU>{data_wplywu}</DATA_WPLYWU>
      <TERMIN>{termin_platnosci}</TERMIN>
      <DATA_DATAOBOWIAZKUPODATKOWEGO>{data_zakupu}</DATA_DATAOBOWIAZKUPODATKOWEGO>
      <DATA_DATAPRAWAODLICZENIA>{data_zakupu}</DATA_DATAPRAWAODLICZENIA>
      <NUMER><![CDATA[{numer_faktury}]]></NUMER>
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
      <PODMIOT><![CDATA[{nazwa_sprzedawcy}]]></PODMIOT>
      <PODMIOT_ID>{str(uuid.uuid4()).upper()}</PODMIOT_ID>
      <PODMIOT_NIP>{nip_sprzedawcy}</PODMIOT_NIP>
      <NAZWA1><![CDATA[{nazwa_sprzedawcy}]]></NAZWA1>
      <NAZWA2></NAZWA2>
      <NAZWA3></NAZWA3>
      <NIP_KRAJ></NIP_KRAJ>
      <NIP>{nip_sprzedawcy}</NIP>
      <KRAJ>{kraj}</KRAJ>
      <WOJEWODZTWO>mazowieckie</WOJEWODZTWO>
      <POWIAT></POWIAT>
      <GMINA></GMINA>
      <ULICA><![CDATA[{ulica}]]></ULICA>
      <NR_DOMU></NR_DOMU>
      <NR_LOKALU></NR_LOKALU>
      <MIASTO><![CDATA[{miasto}]]></MIASTO>
      <KOD_POCZTOWY>{kod_pocztowy}</KOD_POCZTOWY>
      <POCZTA>{miasto}</POCZTA>
      <DODATKOWE></DODATKOWE>
      <PESEL></PESEL>
      <ROLNIK>Nie</ROLNIK>
      <TYP_PLATNIKA>kontrahent</TYP_PLATNIKA>
      <PLATNIK>{nazwa_sprzedawcy}</PLATNIK>
      <PLATNIK_ID>{str(uuid.uuid4()).upper()}</PLATNIK_ID>
      <PLATNIK_NIP>{nip_sprzedawcy}</PLATNIK_NIP>
      <KATEGORIA>402-07-01</KATEGORIA>
      <KATEGORIA_ID>{str(uuid.uuid4()).upper()}</KATEGORIA_ID>
      <OPIS></OPIS>
      <FORMA_PLATNOSCI></FORMA_PLATNOSCI>
      <FORMA_PLATNOSCI_ID></FORMA_PLATNOSCI_ID>
      <DEKLARACJA_VAT7>{data_wystawienia[:7]}</DEKLARACJA_VAT7>
      <DEKLARACJA_VATUE>Nie</DEKLARACJA_VATUE>
      <WALUTA>{waluta}</WALUTA>
      <KURS_WALUTY>NBP</KURS_WALUTY>
      <NOTOWANIE_WALUTY_ILE>1</NOTOWANIE_WALUTY_ILE>
      <NOTOWANIE_WALUTY_ZA_ILE>1</NOTOWANIE_WALUTY_ZA_ILE>
      <DATA_KURSU>{data_zakupu}</DATA_KURSU>
      <KURS_DO_KSIEGOWANIA>Nie</KURS_DO_KSIEGOWANIA>
      <KURS_WALUTY_2>NBP</KURS_WALUTY_2>
      <NOTOWANIE_WALUTY_ILE_2>1</NOTOWANIE_WALUTY_ILE_2>
      <NOTOWANIE_WALUTY_ZA_ILE_2>1</NOTOWANIE_WALUTY_ZA_ILE_2>
      <DATA_KURSU_2>{data_zakupu}</DATA_KURSU_2>
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
          <KATEGORIA_POS>402-07-01</KATEGORIA_POS>
          <KATEGORIA_ID_POS>{str(uuid.uuid4()).upper()}</KATEGORIA_ID_POS>
          <STAWKA_VAT>{int(stawka_vat)}</STAWKA_VAT>
          <STATUS_VAT>opodatkowana</STATUS_VAT>
          <NETTO>{netto:.2f}</NETTO>
          <VAT>{vat:.2f}</VAT>
          <NETTO_SYS>{netto:.2f}</NETTO_SYS>
          <VAT_SYS>{vat:.2f}</VAT_SYS>
          <NETTO_SYS2>{netto:.2f}</NETTO_SYS2>
          <VAT_SYS2>{vat:.2f}</VAT_SYS2>
          <RODZAJ_ZAKUPU>usługi</RODZAJ_ZAKUPU>
          <ODLICZENIA_VAT>tak</ODLICZENIA_VAT>
          <KOLUMNA_KPR>Inne</KOLUMNA_KPR>
          <KOLUMNA_RYCZALT>3.00</KOLUMNA_RYCZALT>
          <OPIS_POZ></OPIS_POZ>
        </POZYCJA>
      </POZYCJE>
      <KWOTY_DODATKOWE></KWOTY_DODATKOWE>
      <PLATNOSCI>
        <PLATNOSC>
          <ID_ZRODLA_PLAT>{platnosc_id}</ID_ZRODLA_PLAT>
          <TERMIN_PLAT>{termin_platnosci}</TERMIN_PLAT>
          <FORMA_PLATNOSCI_PLAT></FORMA_PLATNOSCI_PLAT>
          <FORMA_PLATNOSCI_ID_PLAT></FORMA_PLATNOSCI_ID_PLAT>
          <KWOTA_PLAT>{brutto:.2f}</KWOTA_PLAT>
          <WALUTA_PLAT>{waluta}</WALUTA_PLAT>
          <KURS_WALUTY_PLAT>NBP</KURS_WALUTY_PLAT>
          <NOTOWANIE_WALUTY_ILE_PLAT>1</NOTOWANIE_WALUTY_ILE_PLAT>
          <NOTOWANIE_WALUTY_ZA_ILE_PLAT>1</NOTOWANIE_WALUTY_ZA_ILE_PLAT>
          <KWOTA_PLN_PLAT>{brutto:.2f}</KWOTA_PLN_PLAT>
          <KIERUNEK>rozchód</KIERUNEK>
          <PODLEGA_ROZLICZENIU>tak</PODLEGA_ROZLICZENIU>
          <KONTO></KONTO>
          <NIE_NALICZAJ_ODSETEK>Nie</NIE_NALICZAJ_ODSETEK>
          <PRZELEW_SEPA>Nie</PRZELEW_SEPA>
          <DATA_KURSU_PLAT>{data_zakupu}</DATA_KURSU_PLAT>
          <WALUTA_DOK>{waluta}</WALUTA_DOK>
          <PLATNOSC_TYP_PODMIOTU>kontrahent</PLATNOSC_TYP_PODMIOTU>
          <PLATNOSC_PODMIOT>{nazwa_sprzedawcy}</PLATNOSC_PODMIOT>
          <PLATNOSC_PODMIOT_ID>{str(uuid.uuid4()).upper()}</PLATNOSC_PODMIOT_ID>
          <PLATNOSC_PODMIOT_NIP>{nip_sprzedawcy}</PLATNOSC_PODMIOT_NIP>
          <PLAT_KATEGORIA>402-07-01</PLAT_KATEGORIA>
          <PLAT_KATEGORIA_ID>{str(uuid.uuid4()).upper()}</PLAT_KATEGORIA_ID>
          <PLAT_ELIXIR_O1>Zapłata za {numer_faktury}</PLAT_ELIXIR_O1>
          <PLAT_ELIXIR_O2></PLAT_ELIXIR_O2>
          <PLAT_ELIXIR_O3></PLAT_ELIXIR_O3>
          <PLAT_ELIXIR_O4></PLAT_ELIXIR_O4>
          <PLAT_FA_Z_PA>Nie</PLAT_FA_Z_PA>
          <PLAT_VAN_FA_Z_PA>Nie</PLAT_VAN_FA_Z_PA>
          <PLAT_SPLIT_PAYMENT>Nie</PLAT_SPLIT_PAYMENT>
          <PLAT_SPLIT_KWOTA_VAT>{vat:.2f}</PLAT_SPLIT_KWOTA_VAT>
          <PLAT_SPLIT_NIP>{nip_sprzedawcy}</PLAT_SPLIT_NIP>
          <PLAT_SPLIT_NR_DOKUMENTU>{numer_faktury}</PLAT_SPLIT_NR_DOKUMENTU>
        </PLATNOSC>
      </PLATNOSCI>
      <KODY_JPK></KODY_JPK>
      <ATRYBUTY></ATRYBUTY>
    </REJESTR_ZAKUPU_VAT>
  </REJESTRY_ZAKUPU_VAT>
</ROOT>'''
        
        return xml_content
        
    except Exception as e:
        raise Exception(f"Błąd tworzenia XML: {str(e)}")

@app.route('/test')
def test():
    try:
        test_data = {
            'A': 'TEST/123/2025',
            'B': '45807',  # Excel serial date
            'C': '45807', 
            'D': '45807',
            'E': '45821',  # 14 days later
            'F': '1234567890',
            'G': 'Test Firma Sp. z o.o.',
            'H': 'ul. Testowa 1',
            'I': 'Warszawa',
            'J': '00-001',
            'K': 'Polska',
            'L': '23',
            'M': '1000.00',
            'N': '230.00', 
            'O': '1230.00',
            'P': 'PLN',
            'Q': 'przelew'
        }
        
        xml_result = create_xml(test_data)
        
        return jsonify({
            'success': True,
            'message': 'Test conversion successful',
            'xml_content': xml_result,
            'timestamp': datetime.now().isoformat(),
            'note': 'To jest endpoint testowy - identyfikatory baz: KSIEG/KSIEG'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/convert/single', methods=['POST'])
def convert_single():
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Brak danych JSON'
            }), 400
        
        xml_result = create_xml(data)
        
        return jsonify({
            'success': True,
            'message': 'Conversion successful',
            'xml_content': xml_result,
            'processed_fields': list(data.keys()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc(),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/')
def home():
    return jsonify({
        'message': 'XML Converter API for Comarch Optima',
        'version': '1.2',
        'endpoints': {
            '/test': 'Test conversion with sample data',
            '/convert/single': 'Convert single row (POST)',
        },
        'status': 'ACTIVE - KSIEG identifiers',
        'updated': '2025-06-05'
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
