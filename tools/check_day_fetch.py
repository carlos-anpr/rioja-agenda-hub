import sys
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

def check(date):
    url = f'https://www.elbalcondemateo.es/category/agenda/?f_inicio={date}&f_fin={date}'
    req = Request(url, headers={'User-Agent':'Mozilla/5.0'})
    html = urlopen(req, timeout=20).read().decode('utf-8','ignore')
    soup = BeautifulSoup(html, 'html.parser')
    anchors = soup.select('a[href]')
    cd = soup.select('.cd_item, .cd_item--inner, .cd_item-border--yellow, article, .post, .elementor-post, .listing-item, .event-item, .plan-item')
    markers = ('cuándo','cuando','dónde','donde','hora','edad','precio')
    anchors_with_markers = [a for a in anchors if any(m in (a.get_text(' ',strip=True) or '').lower() for m in markers)]
    print(date)
    print(' total anchors:', len(anchors))
    print(' anchors with markers:', len(anchors_with_markers))
    print(' cd/card nodes:', len(cd))
    print('\n first 20 anchor hrefs:')
    for a in anchors[:20]:
        print('-', a.get('href'), repr((a.get_text(' ',strip=True) or '')[:100]))

if __name__ == "__main__":
    if len(sys.argv)<2:
        print('usage: check_day_fetch.py YYYY-MM-DD')
        sys.exit(1)
    check(sys.argv[1])
