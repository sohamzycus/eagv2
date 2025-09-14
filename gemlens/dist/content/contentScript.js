function u(t){const n=document.createElement("div");return n.innerHTML=t,n.textContent||n.innerText||""}function m(){return window.location.hostname.includes("youtube.com")}class p{extractPageContent(){const n=window.location.href,r=document.title;let e="";const i=["article","main",'[role="main"]',".content","#content",".post-content",".entry-content"];for(const o of i){const a=document.querySelector(o);if(a){e=u(a.innerHTML);break}}if(!e){const o=document.body.cloneNode(!0);["nav","header","footer","aside",".navigation",".nav",".menu",".sidebar",".footer",".header"].forEach(s=>{o.querySelectorAll(s).forEach(d=>d.remove())}),e=u(o.innerHTML)}e=e.replace(/\s+/g," ").trim();const c={text:e,title:r,url:n,type:"webpage"};return m()&&(c.type="video",c.captions=this.extractYouTubeCaptions()),c}extractYouTubeCaptions(){var n,r;try{const e=document.querySelector("ytd-transcript-renderer");if(e){const c=e.querySelectorAll(".segment-text");return Array.from(c).map(o=>o.textContent).join(" ")}const i=document.querySelectorAll("script");for(const c of i){const o=c.textContent||"";if(o.includes("ytInitialPlayerResponse")){const a=o.match(/ytInitialPlayerResponse\s*=\s*({.+?});/);if(a)try{const s=JSON.parse(a[1]),l=(r=(n=s==null?void 0:s.captions)==null?void 0:n.playerCaptionsTracklistRenderer)==null?void 0:r.captionTracks;if(l&&l.length>0)return"Captions available but require additional processing"}catch(s){console.warn("Failed to parse ytInitialPlayerResponse",s)}}}}catch(e){console.warn("Failed to extract YouTube captions",e)}}}const y=new p;chrome.runtime.onMessage.addListener((t,n,r)=>{if(t.action==="extractContent"){try{const e=y.extractPageContent();r({success:!0,content:e})}catch(e){r({success:!1,error:e.message})}return!0}if(t.action==="showOverlay")return x(),r({success:!0}),!0});function x(){if(document.getElementById("gemlens-overlay"))return;const t=document.createElement("iframe");t.id="gemlens-overlay",t.src=chrome.runtime.getURL("content/overlay/overlay.html"),t.style.cssText=`
    position: fixed;
    top: 20px;
    right: 20px;
    width: 400px;
    height: 600px;
    border: none;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    background: white;
  `,document.body.appendChild(t)}console.log("GemLens content script loaded");
