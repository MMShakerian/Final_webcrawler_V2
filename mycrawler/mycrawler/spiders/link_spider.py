import scrapy
import re
from urllib.parse import urlparse, urljoin
from mycrawler.items import PageItem


class LinkSpiderSpider(scrapy.Spider):
    name = "link_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]
    
    def __init__(self, start_url=None, *args, **kwargs):
        super(LinkSpiderSpider, self).__init__(*args, **kwargs)
        
        # Set the start URL if provided
        if start_url:
            self.start_urls = [start_url]
            # Extract domain from the start URL
            parsed_url = urlparse(start_url)
            self.allowed_domains = [parsed_url.netloc]
            
        self.logger.info(f"Starting crawl with domain: {self.allowed_domains[0]}")
        
    def parse(self, response):
        """Process the response and extract links"""
        # Extract the current URL and parent URL
        current_url = response.url
        parent_url = response.meta.get('parent_url', None)
        depth = response.meta.get('depth', 0)
        
        self.logger.info(f"Crawling: {current_url} (depth: {depth})")
        
        # Create a PageItem for the current page
        item = PageItem()
        item['url'] = current_url
        item['parent_url'] = parent_url
        item['title'] = response.css('title::text').get()
        item['status'] = response.status
        item['external'] = False  # This is an internal page since we're crawling it
        item['depth'] = depth
        
        yield item
        
        # Don't continue if we're at max depth
        if depth >= self.settings.getint('DEPTH_LIMIT', 3):
            self.logger.debug(f"Reached max depth for {current_url}")
            return
        
        # Extract all links on the page
        links = response.css('a::attr(href)').getall()
        
        for link in links:
            # Process the URL (handle relative URLs)
            absolute_url = urljoin(response.url, link)
            
            # Parse the URL to get components
            parsed_url = urlparse(absolute_url)
            
            # Skip URLs with no netloc or non-http(s) schemes
            if not parsed_url.netloc or parsed_url.scheme not in ['http', 'https']:
                continue
                
            # Check if the link is internal (same domain)
            is_internal = parsed_url.netloc == self.allowed_domains[0]
            
            # Create an item for external links (but don't follow them)
            if not is_internal:
                ext_item = PageItem()
                ext_item['url'] = absolute_url
                ext_item['parent_url'] = current_url
                ext_item['title'] = None
                ext_item['status'] = None
                ext_item['external'] = True
                ext_item['depth'] = depth + 1
                yield ext_item
                continue
                
            # Skip URL fragments within the same page
            if parsed_url.fragment and parsed_url.path == urlparse(current_url).path:
                continue
                
            # Remove URL fragments for internal page links
            clean_url = absolute_url.split('#')[0]
            
            # Follow internal links
            yield scrapy.Request(
                url=clean_url,
                callback=self.parse,
                meta={
                    'parent_url': current_url,
                    'depth': depth + 1
                }
            )
