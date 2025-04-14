# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import json
import os
from datetime import datetime
from itemadapter import ItemAdapter
from collections import defaultdict
import shutil
from pymongo import MongoClient
from bson import ObjectId
import logging


class TreeBuilderPipeline:
    def __init__(self):
        self.tree = {}  # Changed from defaultdict to regular dict
        self.pages_visited = set()
        self.internal_links = 0
        self.external_links = 0
        self.error_pages = []
        self.domain = ""
        self.stats = {}  # برای ذخیره آمارهای اسپایدر
        self.reports_dir = "reports"
        self.current_report_dir = None
        self.current_report_info = None
        
        # MongoDB connection will be initialized in open_spider
        self.client = None
        self.db = None
        self.pages_collection = None
        self.tree_collection = None
        
    def open_spider(self, spider):
        self.domain = spider.allowed_domains[0]
        # Initialize tree with root URL
        self.tree[spider.start_urls[0]] = {
            'url': spider.start_urls[0],
            'external': False,
            'children': []
        }
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            
        # Create a new report directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_name = self.domain.replace('.', '_')
        self.current_report_dir = os.path.join(self.reports_dir, f"{domain_name}_{timestamp}")
        os.makedirs(self.current_report_dir)
        
        # Initialize report info
        self.current_report_info = {
            "timestamp": datetime.now().isoformat(),
            "domain": self.domain,
            "start_url": spider.start_urls[0],
            "report_dir": self.current_report_dir
        }
        
        # Initialize MongoDB connection with unique database name
        self.client = MongoClient('mongodb://localhost:27017/')
        db_name = f"webcrawler_{domain_name}_{timestamp}"
        self.db = self.client[db_name]
        self.pages_collection = self.db['pages']
        self.tree_collection = self.db['tree_structure']
        
        # Insert root node
        self.tree_collection.insert_one({
            'url': spider.start_urls[0],
            'external': False,
            'children': [],
            'domain': self.domain,
            'timestamp': datetime.now()
        })
        
        # Add database info to report info
        self.current_report_info['database'] = db_name
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get('url')
        status_raw = adapter.get('status')
        logging.info(f"Processing item: {url} (Status raw: {status_raw})")
        
        parent_url = adapter.get('parent_url')
        external = adapter.get('external')
        
        # Count links
        if external:
            self.external_links += 1
        else:
            self.internal_links += 1
            self.pages_visited.add(url)
            
        # Save page data to MongoDB
        page_data = {
            'url': url,
            'parent_url': parent_url,
            'status': status_raw,
            'external': external,
            'domain': self.domain,
            'timestamp': datetime.now()
        }
        self.pages_collection.insert_one(page_data)
        
        # Update tree structure in MongoDB
        if parent_url:
            # Find parent node
            parent_node = self.tree_collection.find_one({'url': parent_url})
            if parent_node:
                # Check if child already exists
                child_exists = any(child['url'] == url for child in parent_node.get('children', []))
                if not child_exists:
                    # Add new child
                    self.tree_collection.update_one(
                        {'url': parent_url},
                        {'$push': {'children': {
                            'url': url,
                            'external': external,
                            'children': []
                        }}}
                    )
            else:
                # If parent not found, create a new root node
                self.tree_collection.insert_one({
                    'url': url,
                    'external': external,
                    'children': [],
                    'domain': self.domain,
                    'timestamp': datetime.now()
                })
        
        # Track error pages
        status = None
        if status_raw is not None:
            try:
                status = int(status_raw)
                if status >= 400:
                    self.error_pages.append({'url': url, 'status': status})
                    logging.info(f"Added error page: {url} (Status: {status})")
            except (ValueError, TypeError):
                logging.warning(f"Could not convert status '{status_raw}' to int for URL: {url}")
            
        return item
                
    def close_spider(self, spider):
        """Generate reports when the spider closes"""
        # ذخیره آمارهای اسپایدر
        self.stats = spider.crawler.stats.get_stats()
        
        # Update report info with statistics
        self.current_report_info.update({
            "total_pages": len(self.pages_visited),
            "internal_links": self.internal_links,
            "external_links": self.external_links,
            "total_requests": self.stats.get('downloader/request_count', 0),
            "total_response_size": self.stats.get('downloader/response_bytes', 0),
            "max_depth": self.stats.get('request_depth_max', 0),
            "duplicate_urls": self.stats.get('dupefilter/filtered', 0),
            "elapsed_time": self.stats.get('elapsed_time_seconds', 0),
            "status_codes": {
                key.split('/')[-1]: value 
                for key, value in self.stats.items() 
                if key.startswith('downloader/response_status_count/')
            },
            "error_pages": self.error_pages,
            "spider_exceptions": self.stats.get('spider_exceptions', {})
        })
        
        # Generate reports
        self._generate_text_report(spider)
        self._generate_json_report(spider)
        self._update_reports_index()
        
        # Close MongoDB connection
        if self.client:
            self.client.close()
            
    def _generate_text_report(self, spider):
        """Generate a text report in tree format"""
        report_path = os.path.join(self.current_report_dir, "report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            # Write report header
            f.write(f"Web Crawler Report\n")
            f.write(f"=================\n\n")
            f.write(f"Timestamp: {self.current_report_info['timestamp']}\n")
            f.write(f"Base Domain: {self.domain}\n")
            f.write(f"Database: {self.current_report_info['database']}\n")
            f.write(f"Total Pages Visited: {len(self.pages_visited)}\n")
            f.write(f"Internal Links: {self.internal_links}\n")
            f.write(f"External Links: {self.external_links}\n\n")
            
            # Write crawl statistics
            f.write(f"Crawl Statistics:\n")
            f.write(f"----------------\n")
            f.write(f"Total Requests: {self.stats.get('downloader/request_count', 0)}\n")
            f.write(f"Total Response Size: {self.stats.get('downloader/response_bytes', 0) / 1024:.2f} KB\n")
            f.write(f"Maximum Depth Reached: {self.stats.get('request_depth_max', 0)}\n")
            f.write(f"Duplicate URLs Filtered: {self.stats.get('dupefilter/filtered', 0)}\n")
            f.write(f"Total Items Scraped: {self.stats.get('item_scraped_count', 0)}\n")
            f.write(f"Elapsed Time: {self.stats.get('elapsed_time_seconds', 0):.2f} seconds\n\n")
            
            # Write HTTP status codes
            f.write(f"HTTP Status Codes:\n")
            f.write(f"-----------------\n")
            status_codes = {k.split('/')[-1]: v for k, v in self.stats.items() if k.startswith('downloader/response_status_count/')}
            # جدا کردن کدهای 200 و سایر کدها
            redirect_codes = [301, 302, 307, 308]
            error_codes = [404, 500, 403, 429]
            # حذف حلقه نادرست که باعث خطا می شود:
            # for item in spider.crawler.stats.get('item_scraped_count', 0): 
            #     pass 

            # راه حل جایگزین: استفاده از self.error_pages و اضافه کردن یک لیست جدید برای ریدایرکت‌ها در process_item
            # **نیاز به تغییر در process_item برای اضافه کردن به self.redirect_pages**

            for code, count in sorted(status_codes.items()):
                 f.write(f"Status {code}: {count} pages\n")
                 # اینجا باید URL ها را از لیست مربوطه بخوانیم
            f.write("\n")
            
            # Write Redirect Pages (3xx)
            redirect_details = defaultdict(list)
            # **فرض می‌کنیم self.redirect_pages در process_item پر شده**
            # for page in self.redirect_pages:
            #     if page['status'] in redirect_codes:
            #         redirect_details[page['status']].append(page['url'])
            # **این کد بالا نیاز به پیاده‌سازی self.redirect_pages دارد**
            
            # **راه حل موقت: نمایش فقط تعداد از آمار**
            redirect_codes_found = {k: v for k, v in status_codes.items() if int(k) in redirect_codes}
            if redirect_codes_found:
                f.write(f"Redirect Pages (Count Only):\n")
                f.write(f"---------------------------\n")
                for code, count in sorted(redirect_codes_found.items()):
                     f.write(f"  Status {code}: {count} pages\n")
                f.write("\n")

            # Write specific error pages (4xx/5xx)
            specific_errors = [404, 500, 403, 429]
            error_details = defaultdict(list)
            for page in self.error_pages:
                if page['status'] in specific_errors:
                    error_details[page['status']].append(page['url'])
            
            if error_details:
                f.write(f"Specific Error Pages:\n")
                f.write(f"---------------------\n")
                for code in specific_errors:
                    if code in error_details:
                        f.write(f"  Status {code}:\n")
                        for url in error_details[code]:
                            f.write(f"    - {url}\n")
                f.write("\n")

            # Write Redirect Information
            redirect_maxdepth = self.stats.get('redirect/maxdepth', 0)
            redirect_loops = self.stats.get('redirect/loops', 0) # Note: Scrapy might not always provide this key directly
            redirect_reasons = {k.split('/')[-1]: v for k, v in self.stats.items() if k.startswith('redirect/reason_count/')}
            
            if redirect_maxdepth > 0 or redirect_loops > 0 or redirect_reasons:
                f.write(f"Redirect Issues:\n")
                f.write(f"----------------\n")
                if redirect_maxdepth > 0:
                    f.write(f"Redirects stopped due to max depth: {redirect_maxdepth}\n")
                if redirect_loops > 0:
                     f.write(f"Detected redirect loops: {redirect_loops}\n") # Add this line
                if redirect_reasons:
                    f.write("Redirect stop reasons:\n")
                    for reason, count in redirect_reasons.items():
                        f.write(f"  - {reason}: {count}\n")
                f.write("\n")
            
            # Write other error pages (>= 400 but not in specific_errors)
            other_errors = []
            for page in self.error_pages:
                if page['status'] not in specific_errors:
                     other_errors.append(page)
                     
            if other_errors:
                f.write(f"Other Error Pages (Status >= 400):\n")
                f.write(f"----------------------------------\n")
                for page in other_errors:
                    f.write(f"  - {page['url']} (Status: {page['status']})\n")
                f.write("\n")
            
            # Write spider exceptions
            spider_exceptions = self.stats.get('spider_exceptions', {})
            if spider_exceptions:
                f.write(f"Spider Exceptions:\n")
                f.write(f"-----------------\n")
                # Use ItemAdapter to handle potential non-dict exceptions if needed
                for exc_type, count in spider_exceptions.items():
                    f.write(f"  - {exc_type}: {count} occurrences\n")
                f.write("\n")
            
            # Write tree structure
            f.write(f"Site Structure:\n")
            f.write(f"---------------\n")
            
            # Get root URL
            root_url = spider.start_urls[0]
            
            # Get tree from MongoDB
            root_node = self.tree_collection.find_one({'url': root_url})
            if root_node:
                f.write(self._format_tree(root_node))
            
    def _format_tree(self, node, prefix=""):
        """Format the tree structure in a readable way"""
        result = []
        
        def _format_branch(node, prefix=""):
            # Add the current node
            node_display = f"{node['url']} [EXTERNAL]" if node.get('external', False) else node['url']
            result.append(f"{prefix}{node_display}")
            
            # Process children
            children = node.get('children', [])
            for i, child in enumerate(children):
                if i == len(children) - 1:  # Last item
                    result.append(f"{prefix}└── {child['url']} [EXTERNAL]" if child.get('external', False) else f"{prefix}└── {child['url']}")
                    if child.get('children'):
                        _format_branch(child, prefix + "    ")
                else:
                    result.append(f"{prefix}├── {child['url']} [EXTERNAL]" if child.get('external', False) else f"{prefix}├── {child['url']}")
                    if child.get('children'):
                        _format_branch(child, prefix + "│   ")
        
        _format_branch(node)
        return "\n".join(result)
            
    def _generate_json_report(self, spider):
        """Generate a JSON report of the tree structure"""
        tree_path = os.path.join(self.current_report_dir, "tree.json")
        
        # Get root node from MongoDB
        root_url = spider.start_urls[0]
        root_node = self.tree_collection.find_one({'url': root_url})
        
        if root_node:
            # Convert ObjectId to string for JSON serialization
            def convert_to_serializable(obj):
                if isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_to_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_serializable(item) for item in obj]
                return obj
            
            serializable_tree = convert_to_serializable(root_node)
            with open(tree_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_tree, f, indent=2)
            
    def _update_reports_index(self):
        """Update the index of all reports"""
        index_path = os.path.join(self.reports_dir, "index.json")
        
        # Load existing index or create new one
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"reports": []}
            
        # Add current report info
        index["reports"].append(self.current_report_info)
        
        # Sort reports by timestamp (newest first)
        index["reports"].sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Save updated index
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
