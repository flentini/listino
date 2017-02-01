#!/usr/bin/env python
import re
import time
import sys

HEADER_START_REGEX = 'X02(.*)'
HEADER_END_REGEX = 'Prezzi\svalidi(.*)'
FOOTER_START_REGEX = 'Listini(.*)'
FOOTER_END_REGEX = 'Pagina(.*)\d'
### anno in corso
YEAR = time.strftime('%y')

## contiene gli errori
ERRORS = []

def get_content(filename):
    file = open(filename)
    return file.read()

def convert_to_array(content):
    return [line.lstrip().rstrip() for line in content.split('\n') if line.strip() != '']

### controlla che il valore sia parsabile come prezzo
def isPrice(value):
    try:
        float(value)
        return True
    except:
        return False

### rimuove header e footer
def slice_content(content, start_rx, end_rx):
    _start_rx = re.compile(start_rx)
    _end_rx = re.compile(end_rx)
    start_index = None
    end_index = None

    for index, token in enumerate(content):
        if re.match(_start_rx, token) and not start_index:
            start_index = index

        if re.match(_end_rx, token) and not end_index:
            end_index = index

        if start_index is not None and end_index is not None:
            del content[start_index:end_index+1]
            start_index = None
            end_index = None

    return content

## rimuove dati inutili, come il trasporto
def remove_useless_data(content):
    return [line for line in content if not (re.match('^Tras\.(.*)$', line) or
        re.match('^Prov\.(.*)$', line) or
        re.match('I0[0-9]', line) or
        line == '0')]

def remove_companies_header(content):
    for index, token in enumerate(content):
        if re.match('(.*)S004\sSEDE-IN-PC', token):
            del content[index-2:index+1]

    return content

def get_companies(content):
    result = []
    start_index = None

    for index, token in enumerate(content):
        if re.match('Destinatario', token):
            if start_index is not None:
                result.append(content[start_index:index])

            start_index = index

    result.append(content[start_index:])
    return result

def split_company_name(content):
    result = []

    for index,token in enumerate(content):
        se = re.search('(.*)S004\sSEDE-IN-PC', token)
        if se is not None and se.group(1) != '':
            result.append(se.group(1))
        result.append(token)

    return result

def reduce_companies(companies):
    result = []

    for company in companies:
        result.append({
            "name": company[2],
            "months": get_company_details_header(company),
            "products": get_products(company)
            })

    return result

def get_company_details_header(company):
    result = []
    start_dates = False
    _year_rx = re.compile('([a-zA-Z].*)'+YEAR+'\-?$')

    for index,token in enumerate(company):
        match = re.match('^Div. UM\s(.*)', token)
        if match:
            start_dates = True
            result.append(match.group(1))
        elif re.match(_year_rx, token) and start_dates:
            result.append(token)

    return result

def get_products(company):
    result = {}
    _gr_rx = re.compile('GRASSI-UNIGRA')
    _start_prices_rx = re.compile('EUR\sTO')
    price_row = False
    product = ''

    for index,token in enumerate(company):
        if re.match(_gr_rx, token):
            result[company[index+1]] = []
            product = company[index+1]
        elif re.match(_start_prices_rx, token):
            price_row = True
        elif price_row:
            if isPrice(token):
                result[product].append(token)
            else:
                price_row = False
                product = token
                result[token] = []

    return result

def raw_print(output):
    for c in output:
        print "======================"
        print c

def align_tab(word, padding):
    return " "*(padding - len(word))

def print_output(output):
    output = reduce_companies(output)

    for company in output:
        print company['name'] + align_tab(company['name'], 70) + "\t\t\t" + "\t".join(company['months'])
        print "\n"
        for product in company['products']:
            print product + align_tab(product, 70) + "\t\t\t" + "\t".join(company['products'][product])

            if (len(company['months']) <> len(company['products'][product])):
                ERRORS.append(company['name'] + ' => ' + product)
        print "======================"

def print_errors():
    if ERRORS:
       print '\nHo trovato incongruenze in ' + str(len(ERRORS)) + ' prodotti, te li devi fare a mano bel:\n'
       for error in ERRORS:
            print error

if sys.argv > 0:
    content_array = convert_to_array(get_content(sys.argv[1]))

    output = slice_content(content_array, FOOTER_START_REGEX, FOOTER_END_REGEX)
    output = slice_content(output, HEADER_START_REGEX, HEADER_END_REGEX)
    output = split_company_name(output)
    output = remove_useless_data(output)
    output = remove_companies_header(output)
    output = get_companies(output)

    print_output(output)
    #raw_print(output)
    print_errors()
