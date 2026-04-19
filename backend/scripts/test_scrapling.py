import sys
import traceback
try:
    from scrapling import StealthyFetcher
    url = "https://www.naukri.com/python-jobs"
    print(f"Scraping {url}")
    page = StealthyFetcher.fetch(url, network_idle=True)
    jobs = page.css('.jobTuple, .srp-jobtuple-wrapper')
    print(f"Found {len(jobs)} job nodes")
    
    for job in jobs[:2]:
        title_node = job.css('a.title')
        comp_node = job.css('a.comp-name, a.subTitle')
        title = title_node[0].text.strip() if title_node else "No title"
        comp = comp_node[0].text.strip() if comp_node else "No comp"
        print(f"Found: {title} at {comp}")
except Exception as e:
    print(f"Error occurred: {e}")
    traceback.print_exc()
