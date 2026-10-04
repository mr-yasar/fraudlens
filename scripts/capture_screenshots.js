const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function capture() {
  const outDir = path.resolve('e:/fraudinvestigation/project_report/assets/screenshots');
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1600,1000']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });

  await page.setRequestInterception(true);
  page.on('request', (req) => {
    const url = req.url();
    if (url.includes('/api/v1/auth/me')) {
      req.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user_id: 1,
          email: 'admin@fraudlens.io',
          name: 'Security Administrator',
          role: 'ADMIN',
          account_tier: 'ENTERPRISE',
          is_active: true
        })
      });
    } else if (url.includes('/api/v1/auth/login')) {
      req.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'valid-mock-jwt-token',
          user_id: 1,
          email: 'admin@fraudlens.io',
          name: 'Security Administrator',
          role: 'ADMIN',
          account_tier: 'ENTERPRISE'
        })
      });
    } else if (url.includes('/api/v1/health')) {
      req.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy', database: 'connected', version: '2.1.1' })
      });
    } else {
      req.continue();
    }
  });

  // Set tokens in localStorage before load
  await page.evaluateOnNewDocument(() => {
    localStorage.setItem('fraudlens_token', 'valid-mock-jwt-token');
    localStorage.setItem('access_token', 'valid-mock-jwt-token');
    localStorage.setItem('fraudlens_user', JSON.stringify({
      id: 1,
      email: 'admin@fraudlens.io',
      name: 'Security Administrator',
      role: 'ADMIN',
      account_tier: 'ENTERPRISE'
    }));
  });

  await page.goto('http://localhost:4173', { waitUntil: 'networkidle0', timeout: 30000 });
  await new Promise(r => setTimeout(r, 3000));

  // Screenshot 17: Dashboard
  await page.screenshot({ path: path.join(outDir, 'screen_17_dashboard.png') });
  console.log('Captured screen_17_dashboard.png');

  // Helper to click by button/nav text
  async function clickNav(text) {
    return await page.evaluate((txt) => {
      const els = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
      const target = els.find(e => e.innerText && e.innerText.includes(txt));
      if (target) {
        target.click();
        return true;
      }
      return false;
    }, text);
  }

  // Screenshot 18: Transaction Risk Analyzer
  let ok = await clickNav('Transaction Risk');
  console.log('Navigated to Risk Analyzer:', ok);
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(outDir, 'screen_18_risk_analyzer.png') });

  // Screenshot 19: Explainable AI & SHAP
  ok = await clickNav('Explainable AI');
  console.log('Navigated to Explainable AI:', ok);
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(outDir, 'screen_19_explainable_ai.png') });

  // Screenshot 20: AI Investigation Copilot / Live Monitor
  ok = await clickNav('AI Investigation');
  if (!ok) ok = await clickNav('Live Transaction');
  console.log('Navigated to Investigations:', ok);
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(outDir, 'screen_20_investigations.png') });

  // Screenshot 21: Model Lab & Registry
  ok = await clickNav('Model Lab');
  console.log('Navigated to Model Lab:', ok);
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(outDir, 'screen_21_model_lab.png') });

  // Screenshot 21b: Database & Storage Health
  ok = await clickNav('Database & Storage');
  console.log('Navigated to Database Health:', ok);
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(outDir, 'screen_21_dataset_health.png') });

  await browser.close();
  console.log('All real application screenshots captured successfully!');
}

capture().catch(console.error);
