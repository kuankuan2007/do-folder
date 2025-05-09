window.addEventListener('load', () => {
  document.querySelectorAll('.highlight pre').forEach((ele) => {
    const codeEle = document.createElement('code');
    codeEle.innerHTML = ele.innerHTML;
    ele.innerHTML = '';
    ele.appendChild(codeEle);
  });
  hljs.highlightAll();
});
