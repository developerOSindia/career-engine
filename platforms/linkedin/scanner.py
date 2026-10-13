"""
LinkedIn Job Search & Extraction Module.
Constructs targeted search URLs and parses search results into structured JobPosting objects.
"""
import asyncio
import urllib.parse
from typing import List, Dict, Optional
from playwright.async_api import Page
from core.models import JobPosting

class LinkedInJobScanner:
    def __init__(self, page: Page):
        self.page = page

    def build_search_url(
        self,
        keywords: str = "Senior Data Engineer",
        location: str = "Bengaluru, Karnataka, India",
        easy_apply: bool = True,
        date_posted: str = "past-week",
        remote: bool = False,
        start: int = 0
    ) -> str:
        """Constructs an optimized LinkedIn job search URL."""
        params = {
            "keywords": keywords,
            "location": location,
            "sortBy": "DD",  # Sort by newest date
        }

        if easy_apply:
            params["f_AL"] = "true"  # Easy Apply filter

        if date_posted == "past-24h":
            params["f_TPR"] = "r86400"
        elif date_posted == "past-week":
            params["f_TPR"] = "r604800"
        elif date_posted == "past-month":
            params["f_TPR"] = "r2592000"

        if remote:
            params["f_WT"] = "2"  # Remote filter

        if start > 0:
            params["start"] = str(start)

        query_string = urllib.parse.urlencode(params)
        return f"https://www.linkedin.com/jobs/search/?{query_string}"

    async def search(self, search_url: str) -> None:
        """Navigates to the search URL and waits for page to load."""
        print(f"🔍 Navigating to LinkedIn Job Search:\n   {search_url}")
        await self.page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4.0)

    async def extract_jobs_on_page(self) -> List[Dict]:
        """Extracts job IDs, titles, companies, and Easy Apply status from the page."""
        jobs_data = await self.page.evaluate(r'''() => {
            const list = [];
            const seen = new Set();
            
            const anchors = Array.from(document.querySelectorAll('a'));
            for (const a of anchors) {
                let jobId = null;
                const href = a.href || '';
                
                if (href.includes('/jobs/view/')) {
                    const match = href.match(/\/jobs\/view\/(\d+)/);
                    if (match) jobId = match[1];
                } else if (href.includes('currentJobId=')) {
                    const match = href.match(/currentJobId=(\d+)/);
                    if (match) jobId = match[1];
                }
                
                if (jobId && !seen.has(jobId)) {
                    seen.add(jobId);
                    const card = a.closest('div[data-job-id], li, .job-card-container, div');
                    const text = (card ? card.innerText : a.innerText).trim();
                    const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
                    
                    const title = lines[0] || 'Data Engineer';
                    const company = lines.length > 1 ? lines[1] : '';
                    const location = lines.length > 2 ? lines[2] : '';
                    const isEasyApply = text.toLowerCase().includes('easy apply');
                    
                    list.push({
                        job_id: jobId,
                        title: title,
                        company: company,
                        location: location,
                        job_url: `https://www.linkedin.com/jobs/view/${jobId}/`,
                        is_easy_apply: isEasyApply
                    });
                }
            }
            return list;
        }''')
        
        return jobs_data
