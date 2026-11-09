const language = document.querySelector('#language');
const photo = document.querySelector('#photo');
function showLanguage(locale) {
  const chinese = locale === 'zh-CN';
  document.documentElement.lang = chinese ? 'zh-CN' : 'en';
  document.title = chinese ? '应鑫雨 · 学术主页' : 'Xinyu Ying · Research';
  language.textContent = chinese ? 'EN' : '中文';
  language.setAttribute('aria-label', chinese ? 'Switch to English' : '切换为中文');
  photo.alt = chinese ? '应鑫雨在中欧国际工商学院校园手持红色中欧小熊' : 'Xinyu Ying holding a red CEIBS teddy bear on campus';
}
try { showLanguage(localStorage.getItem('home-language')); } catch { showLanguage('en'); }
language.hidden = false;
language.addEventListener('click', () => {
  showLanguage(document.documentElement.lang === 'en' ? 'zh-CN' : 'en');
  try { localStorage.setItem('home-language', document.documentElement.lang); } catch {}
});
