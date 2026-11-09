const { chromium } = require('playwright');
(async () => {
  const [file, outPrefix, pdf] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.route('**/*', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
  await p.goto('file://' + file); await p.waitForTimeout(1500);
  const secs = await p.$$('section.sl');
  let i = 0;
  for (const s of secs) { i++; await s.screenshot({ path: outPrefix + String(i).padStart(2,'0') + '.png' }); }
  if (pdf) {
    await p.addStyleTag({ content: '@page{size:1920px 1080px;margin:0} body{background:none} .sl{margin:0 !important;break-after:page}' });
    await p.pdf({ path: pdf, width: '1920px', height: '1080px', printBackground: true, margin: {top:0,right:0,bottom:0,left:0} });
  }
  console.log('shots', i);
  await b.close();
})();
