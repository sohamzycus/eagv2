var U=Object.defineProperty;var F=(e,n,t)=>n in e?U(e,n,{enumerable:!0,configurable:!0,writable:!0,value:t}):e[n]=t;var h=(e,n,t)=>F(e,typeof n!="symbol"?n+"":n,t);/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */var N;(function(e){e.HARM_CATEGORY_UNSPECIFIED="HARM_CATEGORY_UNSPECIFIED",e.HARM_CATEGORY_HATE_SPEECH="HARM_CATEGORY_HATE_SPEECH",e.HARM_CATEGORY_SEXUALLY_EXPLICIT="HARM_CATEGORY_SEXUALLY_EXPLICIT",e.HARM_CATEGORY_HARASSMENT="HARM_CATEGORY_HARASSMENT",e.HARM_CATEGORY_DANGEROUS_CONTENT="HARM_CATEGORY_DANGEROUS_CONTENT"})(N||(N={}));var v;(function(e){e.HARM_BLOCK_THRESHOLD_UNSPECIFIED="HARM_BLOCK_THRESHOLD_UNSPECIFIED",e.BLOCK_LOW_AND_ABOVE="BLOCK_LOW_AND_ABOVE",e.BLOCK_MEDIUM_AND_ABOVE="BLOCK_MEDIUM_AND_ABOVE",e.BLOCK_ONLY_HIGH="BLOCK_ONLY_HIGH",e.BLOCK_NONE="BLOCK_NONE"})(v||(v={}));var M;(function(e){e.HARM_PROBABILITY_UNSPECIFIED="HARM_PROBABILITY_UNSPECIFIED",e.NEGLIGIBLE="NEGLIGIBLE",e.LOW="LOW",e.MEDIUM="MEDIUM",e.HIGH="HIGH"})(M||(M={}));var K;(function(e){e.BLOCKED_REASON_UNSPECIFIED="BLOCKED_REASON_UNSPECIFIED",e.SAFETY="SAFETY",e.OTHER="OTHER"})(K||(K={}));var C;(function(e){e.FINISH_REASON_UNSPECIFIED="FINISH_REASON_UNSPECIFIED",e.STOP="STOP",e.MAX_TOKENS="MAX_TOKENS",e.SAFETY="SAFETY",e.RECITATION="RECITATION",e.OTHER="OTHER"})(C||(C={}));var P;(function(e){e.TASK_TYPE_UNSPECIFIED="TASK_TYPE_UNSPECIFIED",e.RETRIEVAL_QUERY="RETRIEVAL_QUERY",e.RETRIEVAL_DOCUMENT="RETRIEVAL_DOCUMENT",e.SEMANTIC_SIMILARITY="SEMANTIC_SIMILARITY",e.CLASSIFICATION="CLASSIFICATION",e.CLUSTERING="CLUSTERING"})(P||(P={}));/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */class g extends Error{constructor(n){super(`[GoogleGenerativeAI Error]: ${n}`)}}class L extends g{constructor(n,t){super(n),this.response=t}}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const $="https://generativelanguage.googleapis.com",B="v1",j="0.1.3",z="genai-js";var f;(function(e){e.GENERATE_CONTENT="generateContent",e.STREAM_GENERATE_CONTENT="streamGenerateContent",e.COUNT_TOKENS="countTokens",e.EMBED_CONTENT="embedContent",e.BATCH_EMBED_CONTENTS="batchEmbedContents"})(f||(f={}));class y{constructor(n,t,s,r){this.model=n,this.task=t,this.apiKey=s,this.stream=r}toString(){let n=`${$}/${B}/models/${this.model}:${this.task}`;return this.stream&&(n+="?alt=sse"),n}}function J(){return`${z}/${j}`}async function S(e,n){let t;try{if(t=await fetch(e.toString(),{method:"POST",headers:{"Content-Type":"application/json","x-goog-api-client":J(),"x-goog-api-key":e.apiKey},body:n}),!t.ok){let s="";try{const r=await t.json();s=r.error.message,r.error.details&&(s+=` ${JSON.stringify(r.error.details)}`)}catch{}throw new Error(`[${t.status} ${t.statusText}] ${s}`)}}catch(s){const r=new g(`Error fetching from ${e.toString()}: ${s.message}`);throw r.stack=s.stack,r}return t}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function I(e){return e.text=()=>{if(e.candidates&&e.candidates.length>0){if(e.candidates.length>1&&console.warn(`This response had ${e.candidates.length} candidates. Returning text from the first candidate only. Access response.candidates directly to use the other candidates.`),Y(e.candidates[0]))throw new L(`${A(e)}`,e);return V(e)}else if(e.promptFeedback)throw new L(`Text not available. ${A(e)}`,e);return""},e}function V(e){var n,t,s,r;return!((r=(s=(t=(n=e.candidates)===null||n===void 0?void 0:n[0].content)===null||t===void 0?void 0:t.parts)===null||s===void 0?void 0:s[0])===null||r===void 0)&&r.text?e.candidates[0].content.parts[0].text:""}const q=[C.RECITATION,C.SAFETY];function Y(e){return!!e.finishReason&&q.includes(e.finishReason)}function A(e){var n,t,s;let r="";if((!e.candidates||e.candidates.length===0)&&e.promptFeedback)r+="Response was blocked",!((n=e.promptFeedback)===null||n===void 0)&&n.blockReason&&(r+=` due to ${e.promptFeedback.blockReason}`),!((t=e.promptFeedback)===null||t===void 0)&&t.blockReasonMessage&&(r+=`: ${e.promptFeedback.blockReasonMessage}`);else if(!((s=e.candidates)===null||s===void 0)&&s[0]){const o=e.candidates[0];Y(o)&&(r+=`Candidate was blocked due to ${o.finishReason}`,o.finishMessage&&(r+=`: ${o.finishMessage}`))}return r}function _(e){return this instanceof _?(this.v=e,this):new _(e)}function X(e,n,t){if(!Symbol.asyncIterator)throw new TypeError("Symbol.asyncIterator is not defined.");var s=t.apply(e,n||[]),r,o=[];return r={},c("next"),c("throw"),c("return"),r[Symbol.asyncIterator]=function(){return this},r;function c(u){s[u]&&(r[u]=function(E){return new Promise(function(p,k){o.push([u,E,p,k])>1||i(u,E)})})}function i(u,E){try{a(s[u](E))}catch(p){w(o[0][3],p)}}function a(u){u.value instanceof _?Promise.resolve(u.value.v).then(d,O):w(o[0][2],u)}function d(u){i("next",u)}function O(u){i("throw",u)}function w(u,E){u(E),o.shift(),o.length&&i(o[0][0],o[0][1])}}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const G=/^data\: (.*)(?:\n\n|\r\r|\r\n\r\n)/;function W(e){const n=e.body.pipeThrough(new TextDecoderStream("utf8",{fatal:!0})),t=ee(n),[s,r]=t.tee();return{stream:Z(s),response:Q(r)}}async function Q(e){const n=[],t=e.getReader();for(;;){const{done:s,value:r}=await t.read();if(s)return I(te(n));n.push(r)}}function Z(e){return X(this,arguments,function*(){const t=e.getReader();for(;;){const{value:s,done:r}=yield _(t.read());if(r)break;yield yield _(I(s))}})}function ee(e){const n=e.getReader();return new ReadableStream({start(s){let r="";return o();function o(){return n.read().then(({value:c,done:i})=>{if(i){if(r.trim()){s.error(new g("Failed to parse stream"));return}s.close();return}r+=c;let a=r.match(G),d;for(;a;){try{d=JSON.parse(a[1])}catch{s.error(new g(`Error parsing JSON response: "${a[1]}"`));return}s.enqueue(d),r=r.substring(a[0].length),a=r.match(G)}return o()})}}})}function te(e){const n=e[e.length-1],t={promptFeedback:n==null?void 0:n.promptFeedback};for(const s of e)if(s.candidates)for(const r of s.candidates){const o=r.index;if(t.candidates||(t.candidates=[]),t.candidates[o]||(t.candidates[o]={index:r.index}),t.candidates[o].citationMetadata=r.citationMetadata,t.candidates[o].finishReason=r.finishReason,t.candidates[o].finishMessage=r.finishMessage,t.candidates[o].safetyRatings=r.safetyRatings,r.content&&r.content.parts){t.candidates[o].content||(t.candidates[o].content={role:r.content.role||"user",parts:[{text:""}]});for(const c of r.content.parts)c.text&&(t.candidates[o].content.parts[0].text+=c.text)}}return t}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */async function H(e,n,t){const s=new y(n,f.STREAM_GENERATE_CONTENT,e,!0),r=await S(s,JSON.stringify(t));return W(r)}async function D(e,n,t){const s=new y(n,f.GENERATE_CONTENT,e,!1),o=await(await S(s,JSON.stringify(t))).json();return{response:I(o)}}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */function m(e,n){let t=[];if(typeof e=="string")t=[{text:e}];else for(const s of e)typeof s=="string"?t.push({text:s}):t.push(s);return{role:n,parts:t}}function R(e){return e.contents?e:{contents:[m(e,"user")]}}function ne(e){return typeof e=="string"||Array.isArray(e)?{content:m(e,"user")}:e}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */const b="SILENT_ERROR";class se{constructor(n,t,s){this.model=t,this.params=s,this._history=[],this._sendPromise=Promise.resolve(),this._apiKey=n,s!=null&&s.history&&(this._history=s.history.map(r=>{if(!r.role)throw new Error("Missing role for history item: "+JSON.stringify(r));return m(r.parts,r.role)}))}async getHistory(){return await this._sendPromise,this._history}async sendMessage(n){var t,s;await this._sendPromise;const r=m(n,"user"),o={safetySettings:(t=this.params)===null||t===void 0?void 0:t.safetySettings,generationConfig:(s=this.params)===null||s===void 0?void 0:s.generationConfig,contents:[...this._history,r]};let c;return this._sendPromise=this._sendPromise.then(()=>D(this._apiKey,this.model,o)).then(i=>{var a;if(i.response.candidates&&i.response.candidates.length>0){this._history.push(r);const d=Object.assign({parts:[],role:"model"},(a=i.response.candidates)===null||a===void 0?void 0:a[0].content);this._history.push(d)}else{const d=A(i.response);d&&console.warn(`sendMessage() was unsuccessful. ${d}. Inspect response object for details.`)}c=i}),await this._sendPromise,c}async sendMessageStream(n){var t,s;await this._sendPromise;const r=m(n,"user"),o={safetySettings:(t=this.params)===null||t===void 0?void 0:t.safetySettings,generationConfig:(s=this.params)===null||s===void 0?void 0:s.generationConfig,contents:[...this._history,r]},c=H(this._apiKey,this.model,o);return this._sendPromise=this._sendPromise.then(()=>c).catch(i=>{throw new Error(b)}).then(i=>i.response).then(i=>{if(i.candidates&&i.candidates.length>0){this._history.push(r);const a=Object.assign({},i.candidates[0].content);a.role||(a.role="model"),this._history.push(a)}else{const a=A(i);a&&console.warn(`sendMessageStream() was unsuccessful. ${a}. Inspect response object for details.`)}}).catch(i=>{i.message!==b&&console.error(i)}),c}}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */async function re(e,n,t){const s=new y(n,f.COUNT_TOKENS,e,!1);return(await S(s,JSON.stringify(Object.assign(Object.assign({},t),{model:n})))).json()}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */async function oe(e,n,t){const s=new y(n,f.EMBED_CONTENT,e,!1);return(await S(s,JSON.stringify(t))).json()}async function ie(e,n,t){const s=new y(n,f.BATCH_EMBED_CONTENTS,e,!1),r=t.requests.map(c=>Object.assign(Object.assign({},c),{model:`models/${n}`}));return(await S(s,JSON.stringify({requests:r}))).json()}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */class ae{constructor(n,t){var s;this.apiKey=n,t.model.startsWith("models/")?this.model=(s=t.model.split("models/"))===null||s===void 0?void 0:s[1]:this.model=t.model,this.generationConfig=t.generationConfig||{},this.safetySettings=t.safetySettings||[]}async generateContent(n){const t=R(n);return D(this.apiKey,this.model,Object.assign({generationConfig:this.generationConfig,safetySettings:this.safetySettings},t))}async generateContentStream(n){const t=R(n);return H(this.apiKey,this.model,Object.assign({generationConfig:this.generationConfig,safetySettings:this.safetySettings},t))}startChat(n){return new se(this.apiKey,this.model,n)}async countTokens(n){const t=R(n);return re(this.apiKey,this.model,t)}async embedContent(n){const t=ne(n);return oe(this.apiKey,this.model,t)}async batchEmbedContents(n){return ie(this.apiKey,this.model,n)}}/**
 * @license
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */class ce{constructor(n){this.apiKey=n}getGenerativeModel(n){if(!n.model)throw new g("Must provide a model name. Example: genai.getGenerativeModel({ model: 'my-model-name' })");return new ae(this.apiKey,n)}}class ue{constructor(n,t="gemini-1.5-flash"){h(this,"model");this.apiKey=n;const s=new ce(this.apiKey);this.model=s.getGenerativeModel({model:t})}async summarize(n,t){var s;try{return((s=(await this.model.generateContent({contents:[{role:"user",parts:[{text:n}]}],generationConfig:{maxOutputTokens:(t==null?void 0:t.maxTokens)??512}})).response)==null?void 0:s.text())??""}catch(r){throw console.error("GeminiService.summarize error",r),new Error("Gemini summarization failed")}}async streamSummarize(n,t,s){var c;let o=0;for(;o<3;)try{const i=await this.model.generateContentStream({contents:[{role:"user",parts:[{text:n}]}],generationConfig:{maxOutputTokens:(s==null?void 0:s.maxTokens)??512}});for await(const a of i.stream){const d=((c=a==null?void 0:a.text)==null?void 0:c.call(a))??"";d&&t(d)}return}catch(i){o++;const a=300*Math.pow(2,o);if(console.warn(`streamSummarize attempt ${o} failed, retrying in ${a}ms`,i),await new Promise(d=>setTimeout(d,a)),o>=3)throw console.error("streamSummarize failed after retries",i),new Error("Streaming summarization failed")}}}class x{async summarize(n){return"This is a mock summary."}async streamSummarize(n,t){t("Mock stream part 1. "),await new Promise(s=>setTimeout(s,50)),t("Mock stream part 2.")}}class de{constructor(){h(this,"API_KEY_KEY","GEMINI_API_KEY")}async getApiKey(){return new Promise(n=>{chrome.storage.local.get([this.API_KEY_KEY],t=>{n(t[this.API_KEY_KEY]??null)})})}async setApiKey(n){return new Promise(t=>{chrome.storage.local.set({[this.API_KEY_KEY]:n},()=>t())})}async clearApiKey(){return new Promise(n=>{chrome.storage.local.remove([this.API_KEY_KEY],()=>n())})}}class le{constructor(){h(this,"KEY_PREFIX","GEMLENS_CACHE_");h(this,"defaultTtl",24*60*60*1e3)}storageKey(n){return`${this.KEY_PREFIX}${encodeURIComponent(n)}`}async get(n){return new Promise(t=>{chrome.storage.local.get([this.storageKey(n)],s=>{const r=s[this.storageKey(n)];if(!r)return t(null);Date.now()-r.createdAt>(r.ttl??this.defaultTtl)?chrome.storage.local.remove([this.storageKey(n)],()=>t(null)):t(r.value)})})}async set(n,t,s){const r={createdAt:Date.now(),ttl:s??this.defaultTtl,value:t};return new Promise(o=>{chrome.storage.local.set({[this.storageKey(n)]:r},()=>o())})}async invalidate(n){return new Promise(t=>{chrome.storage.local.remove([this.storageKey(n)],()=>t())})}}function T(e=!1,n){const t=new de,s=new le;let r;return e?r=new x:n?r=new ue(n):r=new x,{gemini:r,storage:t,cache:s}}let l=T(!0);(async function(){const t=await l.storage.getApiKey();t&&(l=T(!1,t))})();chrome.runtime.onMessage.addListener((e,n,t)=>((async()=>{try{if(e.action==="summarizePage"){const s=e.url??(n.tab&&n.tab.url)??"unknown",r=await l.cache.get(s);if(r){t({summary:r});return}const o=e.text??"",c=await l.gemini.summarize(o);await l.cache.set(s,c),t({summary:c});return}if(e.action==="streamSummarize"){const s=e.text??"";t({status:"ok"})}if(e.action==="refreshApiKey"){const s=await l.storage.getApiKey();s&&(l=T(!1,s)),t({ok:!0});return}}catch(s){console.error("service_worker message handler error",s),t({error:s.message??"Unknown error"})}})(),!0));chrome.runtime.onConnect.addListener(e=>{e.name==="gemini-stream"&&e.onMessage.addListener(async n=>{if(n.action==="streamSummarize")try{const t=n.text??"";await l.gemini.streamSummarize(t,s=>{e.postMessage({type:"delta",chunk:s})}),e.postMessage({type:"complete"})}catch(t){e.postMessage({type:"error",error:t.message})}})});
