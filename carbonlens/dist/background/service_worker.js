/**
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
 */
var HarmCategory;
(function(HarmCategory2) {
  HarmCategory2["HARM_CATEGORY_UNSPECIFIED"] = "HARM_CATEGORY_UNSPECIFIED";
  HarmCategory2["HARM_CATEGORY_HATE_SPEECH"] = "HARM_CATEGORY_HATE_SPEECH";
  HarmCategory2["HARM_CATEGORY_SEXUALLY_EXPLICIT"] = "HARM_CATEGORY_SEXUALLY_EXPLICIT";
  HarmCategory2["HARM_CATEGORY_HARASSMENT"] = "HARM_CATEGORY_HARASSMENT";
  HarmCategory2["HARM_CATEGORY_DANGEROUS_CONTENT"] = "HARM_CATEGORY_DANGEROUS_CONTENT";
})(HarmCategory || (HarmCategory = {}));
var HarmBlockThreshold;
(function(HarmBlockThreshold2) {
  HarmBlockThreshold2["HARM_BLOCK_THRESHOLD_UNSPECIFIED"] = "HARM_BLOCK_THRESHOLD_UNSPECIFIED";
  HarmBlockThreshold2["BLOCK_LOW_AND_ABOVE"] = "BLOCK_LOW_AND_ABOVE";
  HarmBlockThreshold2["BLOCK_MEDIUM_AND_ABOVE"] = "BLOCK_MEDIUM_AND_ABOVE";
  HarmBlockThreshold2["BLOCK_ONLY_HIGH"] = "BLOCK_ONLY_HIGH";
  HarmBlockThreshold2["BLOCK_NONE"] = "BLOCK_NONE";
})(HarmBlockThreshold || (HarmBlockThreshold = {}));
var HarmProbability;
(function(HarmProbability2) {
  HarmProbability2["HARM_PROBABILITY_UNSPECIFIED"] = "HARM_PROBABILITY_UNSPECIFIED";
  HarmProbability2["NEGLIGIBLE"] = "NEGLIGIBLE";
  HarmProbability2["LOW"] = "LOW";
  HarmProbability2["MEDIUM"] = "MEDIUM";
  HarmProbability2["HIGH"] = "HIGH";
})(HarmProbability || (HarmProbability = {}));
var BlockReason;
(function(BlockReason2) {
  BlockReason2["BLOCKED_REASON_UNSPECIFIED"] = "BLOCKED_REASON_UNSPECIFIED";
  BlockReason2["SAFETY"] = "SAFETY";
  BlockReason2["OTHER"] = "OTHER";
})(BlockReason || (BlockReason = {}));
var FinishReason;
(function(FinishReason2) {
  FinishReason2["FINISH_REASON_UNSPECIFIED"] = "FINISH_REASON_UNSPECIFIED";
  FinishReason2["STOP"] = "STOP";
  FinishReason2["MAX_TOKENS"] = "MAX_TOKENS";
  FinishReason2["SAFETY"] = "SAFETY";
  FinishReason2["RECITATION"] = "RECITATION";
  FinishReason2["OTHER"] = "OTHER";
})(FinishReason || (FinishReason = {}));
var TaskType;
(function(TaskType2) {
  TaskType2["TASK_TYPE_UNSPECIFIED"] = "TASK_TYPE_UNSPECIFIED";
  TaskType2["RETRIEVAL_QUERY"] = "RETRIEVAL_QUERY";
  TaskType2["RETRIEVAL_DOCUMENT"] = "RETRIEVAL_DOCUMENT";
  TaskType2["SEMANTIC_SIMILARITY"] = "SEMANTIC_SIMILARITY";
  TaskType2["CLASSIFICATION"] = "CLASSIFICATION";
  TaskType2["CLUSTERING"] = "CLUSTERING";
})(TaskType || (TaskType = {}));
/**
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
 */
class GoogleGenerativeAIError extends Error {
  constructor(message) {
    super(`[GoogleGenerativeAI Error]: ${message}`);
  }
}
class GoogleGenerativeAIResponseError extends GoogleGenerativeAIError {
  constructor(message, response) {
    super(message);
    this.response = response;
  }
}
/**
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
 */
const BASE_URL = "https://generativelanguage.googleapis.com";
const API_VERSION = "v1";
const PACKAGE_VERSION = "0.2.1";
const PACKAGE_LOG_HEADER = "genai-js";
var Task;
(function(Task2) {
  Task2["GENERATE_CONTENT"] = "generateContent";
  Task2["STREAM_GENERATE_CONTENT"] = "streamGenerateContent";
  Task2["COUNT_TOKENS"] = "countTokens";
  Task2["EMBED_CONTENT"] = "embedContent";
  Task2["BATCH_EMBED_CONTENTS"] = "batchEmbedContents";
})(Task || (Task = {}));
class RequestUrl {
  constructor(model, task, apiKey, stream) {
    this.model = model;
    this.task = task;
    this.apiKey = apiKey;
    this.stream = stream;
  }
  toString() {
    let url = `${BASE_URL}/${API_VERSION}/${this.model}:${this.task}`;
    if (this.stream) {
      url += "?alt=sse";
    }
    return url;
  }
}
function getClientHeaders() {
  return `${PACKAGE_LOG_HEADER}/${PACKAGE_VERSION}`;
}
async function makeRequest(url, body, requestOptions) {
  let response;
  try {
    response = await fetch(url.toString(), Object.assign(Object.assign({}, buildFetchOptions(requestOptions)), { method: "POST", headers: {
      "Content-Type": "application/json",
      "x-goog-api-client": getClientHeaders(),
      "x-goog-api-key": url.apiKey
    }, body }));
    if (!response.ok) {
      let message = "";
      try {
        const json = await response.json();
        message = json.error.message;
        if (json.error.details) {
          message += ` ${JSON.stringify(json.error.details)}`;
        }
      } catch (e) {
      }
      throw new Error(`[${response.status} ${response.statusText}] ${message}`);
    }
  } catch (e) {
    const err = new GoogleGenerativeAIError(`Error fetching from ${url.toString()}: ${e.message}`);
    err.stack = e.stack;
    throw err;
  }
  return response;
}
function buildFetchOptions(requestOptions) {
  const fetchOptions = {};
  if ((requestOptions === null || requestOptions === void 0 ? void 0 : requestOptions.timeout) >= 0) {
    const abortController = new AbortController();
    const signal = abortController.signal;
    setTimeout(() => abortController.abort(), requestOptions.timeout);
    fetchOptions.signal = signal;
  }
  return fetchOptions;
}
/**
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
 */
function addHelpers(response) {
  response.text = () => {
    if (response.candidates && response.candidates.length > 0) {
      if (response.candidates.length > 1) {
        console.warn(`This response had ${response.candidates.length} candidates. Returning text from the first candidate only. Access response.candidates directly to use the other candidates.`);
      }
      if (hadBadFinishReason(response.candidates[0])) {
        throw new GoogleGenerativeAIResponseError(`${formatBlockErrorMessage(response)}`, response);
      }
      return getText(response);
    } else if (response.promptFeedback) {
      throw new GoogleGenerativeAIResponseError(`Text not available. ${formatBlockErrorMessage(response)}`, response);
    }
    return "";
  };
  return response;
}
function getText(response) {
  var _a, _b, _c, _d;
  if ((_d = (_c = (_b = (_a = response.candidates) === null || _a === void 0 ? void 0 : _a[0].content) === null || _b === void 0 ? void 0 : _b.parts) === null || _c === void 0 ? void 0 : _c[0]) === null || _d === void 0 ? void 0 : _d.text) {
    return response.candidates[0].content.parts[0].text;
  } else {
    return "";
  }
}
const badFinishReasons = [FinishReason.RECITATION, FinishReason.SAFETY];
function hadBadFinishReason(candidate) {
  return !!candidate.finishReason && badFinishReasons.includes(candidate.finishReason);
}
function formatBlockErrorMessage(response) {
  var _a, _b, _c;
  let message = "";
  if ((!response.candidates || response.candidates.length === 0) && response.promptFeedback) {
    message += "Response was blocked";
    if ((_a = response.promptFeedback) === null || _a === void 0 ? void 0 : _a.blockReason) {
      message += ` due to ${response.promptFeedback.blockReason}`;
    }
    if ((_b = response.promptFeedback) === null || _b === void 0 ? void 0 : _b.blockReasonMessage) {
      message += `: ${response.promptFeedback.blockReasonMessage}`;
    }
  } else if ((_c = response.candidates) === null || _c === void 0 ? void 0 : _c[0]) {
    const firstCandidate = response.candidates[0];
    if (hadBadFinishReason(firstCandidate)) {
      message += `Candidate was blocked due to ${firstCandidate.finishReason}`;
      if (firstCandidate.finishMessage) {
        message += `: ${firstCandidate.finishMessage}`;
      }
    }
  }
  return message;
}
function __await(v) {
  return this instanceof __await ? (this.v = v, this) : new __await(v);
}
function __asyncGenerator(thisArg, _arguments, generator) {
  if (!Symbol.asyncIterator) throw new TypeError("Symbol.asyncIterator is not defined.");
  var g = generator.apply(thisArg, _arguments || []), i, q = [];
  return i = {}, verb("next"), verb("throw"), verb("return"), i[Symbol.asyncIterator] = function() {
    return this;
  }, i;
  function verb(n) {
    if (g[n]) i[n] = function(v) {
      return new Promise(function(a, b) {
        q.push([n, v, a, b]) > 1 || resume(n, v);
      });
    };
  }
  function resume(n, v) {
    try {
      step(g[n](v));
    } catch (e) {
      settle(q[0][3], e);
    }
  }
  function step(r) {
    r.value instanceof __await ? Promise.resolve(r.value.v).then(fulfill, reject) : settle(q[0][2], r);
  }
  function fulfill(value) {
    resume("next", value);
  }
  function reject(value) {
    resume("throw", value);
  }
  function settle(f, v) {
    if (f(v), q.shift(), q.length) resume(q[0][0], q[0][1]);
  }
}
typeof SuppressedError === "function" ? SuppressedError : function(error, suppressed, message) {
  var e = new Error(message);
  return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
};
/**
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
 */
const responseLineRE = /^data\: (.*)(?:\n\n|\r\r|\r\n\r\n)/;
function processStream(response) {
  const inputStream = response.body.pipeThrough(new TextDecoderStream("utf8", { fatal: true }));
  const responseStream = getResponseStream(inputStream);
  const [stream1, stream2] = responseStream.tee();
  return {
    stream: generateResponseSequence(stream1),
    response: getResponsePromise(stream2)
  };
}
async function getResponsePromise(stream) {
  const allResponses = [];
  const reader = stream.getReader();
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      return addHelpers(aggregateResponses(allResponses));
    }
    allResponses.push(value);
  }
}
function generateResponseSequence(stream) {
  return __asyncGenerator(this, arguments, function* generateResponseSequence_1() {
    const reader = stream.getReader();
    while (true) {
      const { value, done } = yield __await(reader.read());
      if (done) {
        break;
      }
      yield yield __await(addHelpers(value));
    }
  });
}
function getResponseStream(inputStream) {
  const reader = inputStream.getReader();
  const stream = new ReadableStream({
    start(controller) {
      let currentText = "";
      return pump();
      function pump() {
        return reader.read().then(({ value, done }) => {
          if (done) {
            if (currentText.trim()) {
              controller.error(new GoogleGenerativeAIError("Failed to parse stream"));
              return;
            }
            controller.close();
            return;
          }
          currentText += value;
          let match = currentText.match(responseLineRE);
          let parsedResponse;
          while (match) {
            try {
              parsedResponse = JSON.parse(match[1]);
            } catch (e) {
              controller.error(new GoogleGenerativeAIError(`Error parsing JSON response: "${match[1]}"`));
              return;
            }
            controller.enqueue(parsedResponse);
            currentText = currentText.substring(match[0].length);
            match = currentText.match(responseLineRE);
          }
          return pump();
        });
      }
    }
  });
  return stream;
}
function aggregateResponses(responses) {
  const lastResponse = responses[responses.length - 1];
  const aggregatedResponse = {
    promptFeedback: lastResponse === null || lastResponse === void 0 ? void 0 : lastResponse.promptFeedback
  };
  for (const response of responses) {
    if (response.candidates) {
      for (const candidate of response.candidates) {
        const i = candidate.index;
        if (!aggregatedResponse.candidates) {
          aggregatedResponse.candidates = [];
        }
        if (!aggregatedResponse.candidates[i]) {
          aggregatedResponse.candidates[i] = {
            index: candidate.index
          };
        }
        aggregatedResponse.candidates[i].citationMetadata = candidate.citationMetadata;
        aggregatedResponse.candidates[i].finishReason = candidate.finishReason;
        aggregatedResponse.candidates[i].finishMessage = candidate.finishMessage;
        aggregatedResponse.candidates[i].safetyRatings = candidate.safetyRatings;
        if (candidate.content && candidate.content.parts) {
          if (!aggregatedResponse.candidates[i].content) {
            aggregatedResponse.candidates[i].content = {
              role: candidate.content.role || "user",
              parts: [{ text: "" }]
            };
          }
          for (const part of candidate.content.parts) {
            if (part.text) {
              aggregatedResponse.candidates[i].content.parts[0].text += part.text;
            }
          }
        }
      }
    }
  }
  return aggregatedResponse;
}
/**
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
 */
async function generateContentStream(apiKey, model, params, requestOptions) {
  const url = new RequestUrl(
    model,
    Task.STREAM_GENERATE_CONTENT,
    apiKey,
    /* stream */
    true
  );
  const response = await makeRequest(url, JSON.stringify(params), requestOptions);
  return processStream(response);
}
async function generateContent(apiKey, model, params, requestOptions) {
  const url = new RequestUrl(
    model,
    Task.GENERATE_CONTENT,
    apiKey,
    /* stream */
    false
  );
  const response = await makeRequest(url, JSON.stringify(params), requestOptions);
  const responseJson = await response.json();
  const enhancedResponse = addHelpers(responseJson);
  return {
    response: enhancedResponse
  };
}
/**
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
 */
function formatNewContent(request, role) {
  let newParts = [];
  if (typeof request === "string") {
    newParts = [{ text: request }];
  } else {
    for (const partOrString of request) {
      if (typeof partOrString === "string") {
        newParts.push({ text: partOrString });
      } else {
        newParts.push(partOrString);
      }
    }
  }
  return { role, parts: newParts };
}
function formatGenerateContentInput(params) {
  if (params.contents) {
    return params;
  } else {
    const content = formatNewContent(params, "user");
    return { contents: [content] };
  }
}
function formatEmbedContentInput(params) {
  if (typeof params === "string" || Array.isArray(params)) {
    const content = formatNewContent(params, "user");
    return { content };
  }
  return params;
}
/**
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
 */
const SILENT_ERROR = "SILENT_ERROR";
class ChatSession {
  constructor(apiKey, model, params, requestOptions) {
    this.model = model;
    this.params = params;
    this.requestOptions = requestOptions;
    this._history = [];
    this._sendPromise = Promise.resolve();
    this._apiKey = apiKey;
    if (params === null || params === void 0 ? void 0 : params.history) {
      this._history = params.history.map((content) => {
        if (!content.role) {
          throw new Error("Missing role for history item: " + JSON.stringify(content));
        }
        return formatNewContent(content.parts, content.role);
      });
    }
  }
  /**
   * Gets the chat history so far. Blocked prompts are not added to history.
   * Blocked candidates are not added to history, nor are the prompts that
   * generated them.
   */
  async getHistory() {
    await this._sendPromise;
    return this._history;
  }
  /**
   * Sends a chat message and receives a non-streaming
   * {@link GenerateContentResult}
   */
  async sendMessage(request) {
    var _a, _b;
    await this._sendPromise;
    const newContent = formatNewContent(request, "user");
    const generateContentRequest = {
      safetySettings: (_a = this.params) === null || _a === void 0 ? void 0 : _a.safetySettings,
      generationConfig: (_b = this.params) === null || _b === void 0 ? void 0 : _b.generationConfig,
      contents: [...this._history, newContent]
    };
    let finalResult;
    this._sendPromise = this._sendPromise.then(() => generateContent(this._apiKey, this.model, generateContentRequest, this.requestOptions)).then((result) => {
      var _a2;
      if (result.response.candidates && result.response.candidates.length > 0) {
        this._history.push(newContent);
        const responseContent = Object.assign({
          parts: [],
          // Response seems to come back without a role set.
          role: "model"
        }, (_a2 = result.response.candidates) === null || _a2 === void 0 ? void 0 : _a2[0].content);
        this._history.push(responseContent);
      } else {
        const blockErrorMessage = formatBlockErrorMessage(result.response);
        if (blockErrorMessage) {
          console.warn(`sendMessage() was unsuccessful. ${blockErrorMessage}. Inspect response object for details.`);
        }
      }
      finalResult = result;
    });
    await this._sendPromise;
    return finalResult;
  }
  /**
   * Sends a chat message and receives the response as a
   * {@link GenerateContentStreamResult} containing an iterable stream
   * and a response promise.
   */
  async sendMessageStream(request) {
    var _a, _b;
    await this._sendPromise;
    const newContent = formatNewContent(request, "user");
    const generateContentRequest = {
      safetySettings: (_a = this.params) === null || _a === void 0 ? void 0 : _a.safetySettings,
      generationConfig: (_b = this.params) === null || _b === void 0 ? void 0 : _b.generationConfig,
      contents: [...this._history, newContent]
    };
    const streamPromise = generateContentStream(this._apiKey, this.model, generateContentRequest, this.requestOptions);
    this._sendPromise = this._sendPromise.then(() => streamPromise).catch((_ignored) => {
      throw new Error(SILENT_ERROR);
    }).then((streamResult) => streamResult.response).then((response) => {
      if (response.candidates && response.candidates.length > 0) {
        this._history.push(newContent);
        const responseContent = Object.assign({}, response.candidates[0].content);
        if (!responseContent.role) {
          responseContent.role = "model";
        }
        this._history.push(responseContent);
      } else {
        const blockErrorMessage = formatBlockErrorMessage(response);
        if (blockErrorMessage) {
          console.warn(`sendMessageStream() was unsuccessful. ${blockErrorMessage}. Inspect response object for details.`);
        }
      }
    }).catch((e) => {
      if (e.message !== SILENT_ERROR) {
        console.error(e);
      }
    });
    return streamPromise;
  }
}
/**
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
 */
async function countTokens(apiKey, model, params, requestOptions) {
  const url = new RequestUrl(model, Task.COUNT_TOKENS, apiKey, false);
  const response = await makeRequest(url, JSON.stringify(Object.assign(Object.assign({}, params), { model })), requestOptions);
  return response.json();
}
/**
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
 */
async function embedContent(apiKey, model, params, requestOptions) {
  const url = new RequestUrl(model, Task.EMBED_CONTENT, apiKey, false);
  const response = await makeRequest(url, JSON.stringify(params), requestOptions);
  return response.json();
}
async function batchEmbedContents(apiKey, model, params, requestOptions) {
  const url = new RequestUrl(model, Task.BATCH_EMBED_CONTENTS, apiKey, false);
  const requestsWithModel = params.requests.map((request) => {
    return Object.assign(Object.assign({}, request), { model });
  });
  const response = await makeRequest(url, JSON.stringify({ requests: requestsWithModel }), requestOptions);
  return response.json();
}
/**
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
 */
class GenerativeModel {
  constructor(apiKey, modelParams, requestOptions) {
    this.apiKey = apiKey;
    if (modelParams.model.includes("/")) {
      this.model = modelParams.model;
    } else {
      this.model = `models/${modelParams.model}`;
    }
    this.generationConfig = modelParams.generationConfig || {};
    this.safetySettings = modelParams.safetySettings || [];
    this.requestOptions = requestOptions || {};
  }
  /**
   * Makes a single non-streaming call to the model
   * and returns an object containing a single {@link GenerateContentResponse}.
   */
  async generateContent(request) {
    const formattedParams = formatGenerateContentInput(request);
    return generateContent(this.apiKey, this.model, Object.assign({ generationConfig: this.generationConfig, safetySettings: this.safetySettings }, formattedParams), this.requestOptions);
  }
  /**
   * Makes a single streaming call to the model
   * and returns an object containing an iterable stream that iterates
   * over all chunks in the streaming response as well as
   * a promise that returns the final aggregated response.
   */
  async generateContentStream(request) {
    const formattedParams = formatGenerateContentInput(request);
    return generateContentStream(this.apiKey, this.model, Object.assign({ generationConfig: this.generationConfig, safetySettings: this.safetySettings }, formattedParams), this.requestOptions);
  }
  /**
   * Gets a new {@link ChatSession} instance which can be used for
   * multi-turn chats.
   */
  startChat(startChatParams) {
    return new ChatSession(this.apiKey, this.model, startChatParams, this.requestOptions);
  }
  /**
   * Counts the tokens in the provided request.
   */
  async countTokens(request) {
    const formattedParams = formatGenerateContentInput(request);
    return countTokens(this.apiKey, this.model, formattedParams);
  }
  /**
   * Embeds the provided content.
   */
  async embedContent(request) {
    const formattedParams = formatEmbedContentInput(request);
    return embedContent(this.apiKey, this.model, formattedParams);
  }
  /**
   * Embeds an array of {@link EmbedContentRequest}s.
   */
  async batchEmbedContents(batchEmbedContentRequest) {
    return batchEmbedContents(this.apiKey, this.model, batchEmbedContentRequest, this.requestOptions);
  }
}
/**
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
 */
class GoogleGenerativeAI {
  constructor(apiKey) {
    this.apiKey = apiKey;
  }
  /**
   * Gets a {@link GenerativeModel} instance for the provided model name.
   */
  getGenerativeModel(modelParams, requestOptions) {
    if (!modelParams.model) {
      throw new GoogleGenerativeAIError(`Must provide a model name. Example: genai.getGenerativeModel({ model: 'my-model-name' })`);
    }
    return new GenerativeModel(this.apiKey, modelParams, requestOptions);
  }
}
function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
async function retryWithBackoff(fn, maxRetries = 3, baseDelay = 1e3) {
  let lastError;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (attempt === maxRetries) {
        throw lastError;
      }
      const delayMs = baseDelay * Math.pow(2, attempt);
      await delay(delayMs);
    }
  }
  throw lastError;
}
function safeJsonParse(json, fallback) {
  try {
    return JSON.parse(json);
  } catch {
    return fallback;
  }
}
function calculateConfidenceInterval(mean, std, confidence = 0.95) {
  const zScore = confidence === 0.95 ? 1.96 : confidence === 0.99 ? 2.58 : 1.64;
  const margin = zScore * std;
  return [mean - margin, mean + margin];
}
class GeminiService {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.genAI = null;
    this.model = null;
    if (apiKey) {
      this.genAI = new GoogleGenerativeAI(apiKey);
      this.model = this.genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });
    }
  }
  /**
   * Initialize with API key
   */
  initialize(apiKey) {
    this.apiKey = apiKey;
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({ model: "gemini-2.0-flash-exp" });
  }
  /**
   * Generate agent plan from conversation history
   */
  async plan(conversationHistory, options = {}) {
    if (!this.model) {
      throw new Error("Gemini service not initialized with API key");
    }
    const systemPrompt = this.buildSystemPrompt();
    const conversationText = conversationHistory.join("\n\n");
    const fullPrompt = `${systemPrompt}

Conversation History:
${conversationText}

Provide your response as valid JSON only:`;
    try {
      const result = await retryWithBackoff(async () => {
        const response = await this.model.generateContent({
          contents: [{ role: "user", parts: [{ text: fullPrompt }] }],
          generationConfig: {
            maxOutputTokens: options.maxTokens ?? 1024,
            temperature: options.temperature ?? 0.7,
            topP: options.topP ?? 0.8,
            topK: options.topK ?? 40
          }
        });
        const text = response.response.text();
        if (!text) {
          throw new Error("Empty response from Gemini");
        }
        return text;
      });
      const plan = this.parseAgentPlan(result);
      if (!plan) {
        const jsonPrompt = `${fullPrompt}

Your previous response was not valid JSON. Please respond with ONLY valid JSON in the exact format specified above.`;
        const retryResult = await retryWithBackoff(async () => {
          const response = await this.model.generateContent({
            contents: [{ role: "user", parts: [{ text: jsonPrompt }] }],
            generationConfig: {
              maxOutputTokens: options.maxTokens ?? 1024,
              temperature: 0.3,
              // Lower temperature for more structured output
              topP: options.topP ?? 0.8,
              topK: options.topK ?? 40
            }
          });
          return response.response.text();
        });
        const retryPlan = this.parseAgentPlan(retryResult);
        if (!retryPlan) {
          throw new Error("Failed to get valid JSON response from Gemini after retry");
        }
        return retryPlan;
      }
      return plan;
    } catch (error) {
      console.error("Gemini plan generation failed:", error);
      throw new Error(`Gemini API error: ${error.message}`);
    }
  }
  /**
   * Generate summary of text
   */
  async summarize(text, options = {}) {
    if (!this.model) {
      throw new Error("Gemini service not initialized with API key");
    }
    const prompt = `Please provide a concise summary of the following text, focusing on key carbon emissions and environmental impact information:

${text}`;
    try {
      const result = await retryWithBackoff(async () => {
        const response = await this.model.generateContent({
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: {
            maxOutputTokens: options.maxTokens ?? 512,
            temperature: options.temperature ?? 0.5,
            topP: options.topP ?? 0.8,
            topK: options.topK ?? 40
          }
        });
        const text2 = response.response.text();
        if (!text2) {
          throw new Error("Empty response from Gemini");
        }
        return text2;
      });
      return result;
    } catch (error) {
      console.error("Gemini summarization failed:", error);
      throw new Error(`Gemini API error: ${error.message}`);
    }
  }
  /**
   * Stream agent plan with real-time updates
   */
  async streamPlan(conversationHistory, onDelta, options = {}) {
    if (!this.model) {
      throw new Error("Gemini service not initialized with API key");
    }
    const systemPrompt = this.buildSystemPrompt();
    const conversationText = conversationHistory.join("\n\n");
    const fullPrompt = `${systemPrompt}

Conversation History:
${conversationText}

Provide your response as valid JSON only:`;
    try {
      const result = await this.model.generateContentStream({
        contents: [{ role: "user", parts: [{ text: fullPrompt }] }],
        generationConfig: {
          maxOutputTokens: options.maxTokens ?? 1024,
          temperature: options.temperature ?? 0.7,
          topP: options.topP ?? 0.8,
          topK: options.topK ?? 40
        }
      });
      for await (const chunk of result.stream) {
        const chunkText = chunk.text();
        if (chunkText) {
          onDelta(chunkText);
        }
      }
    } catch (error) {
      console.error("Gemini streaming failed:", error);
      throw new Error(`Gemini streaming error: ${error.message}`);
    }
  }
  /**
   * Check if service is configured
   */
  async isConfigured() {
    return this.model !== null && this.apiKey !== void 0;
  }
  /**
   * Build system prompt for agent planning
   */
  buildSystemPrompt() {
    return `You are CarbonLens, an expert carbon emissions research and decision assistant. Your role is to help users analyze, compare, and make decisions about carbon emissions across different technologies, regions, and scenarios.

Available Tools:
- CarbonApiTool: Query carbon emission factors from databases
- LCADatabaseTool: Access life cycle assessment data
- ElectricityIntensityTool: Get regional electricity grid carbon intensity
- NewsSearchTool: Search for recent carbon/climate news and reports
- EmissionEstimatorTool: Perform Monte Carlo emission calculations
- NotifierTool: Send notifications via configured channels
- PageExtractorTool: Extract structured data from current webpage

Response Format:
You must respond with valid JSON in one of these formats:

For tool calls:
{
  "type": "tool_call",
  "tool": "ToolName",
  "args": { "param1": "value1", "param2": "value2" },
  "reasoning": "Why this tool call is needed"
}

For final responses:
{
  "type": "final",
  "response": "Your final answer with analysis and recommendations",
  "reasoning": "Summary of analysis performed"
}

Guidelines:
- Always provide reasoning for your decisions
- Use multiple tools when needed for comprehensive analysis
- Focus on actionable insights and clear comparisons
- Include uncertainty ranges when available
- Cite data sources in your final responses`;
  }
  /**
   * Parse agent plan from response text
   */
  parseAgentPlan(text) {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return null;
    }
    const plan = safeJsonParse(jsonMatch[0], null);
    if (!plan || !plan.type || plan.type !== "tool_call" && plan.type !== "final") {
      return null;
    }
    if (plan.type === "tool_call" && (!plan.tool || !plan.args)) {
      return null;
    }
    if (plan.type === "final" && !plan.response) {
      return null;
    }
    return plan;
  }
}
class GeminiMock {
  constructor() {
    this.callCount = 0;
    this.planResponses = [
      {
        type: "tool_call",
        tool: "CarbonApiTool",
        args: { region: "ap-south1", service: "compute", instanceType: "8-vCPU" },
        reasoning: "Need to get carbon factors for ap-south1 compute instances"
      },
      {
        type: "tool_call",
        tool: "CarbonApiTool",
        args: { region: "eu-west1", service: "compute", instanceType: "8-vCPU" },
        reasoning: "Need to get carbon factors for eu-west1 compute instances for comparison"
      },
      {
        type: "tool_call",
        tool: "EmissionEstimatorTool",
        args: {
          scenarios: [
            { region: "ap-south1", instances: 200, factor: 0.82 },
            { region: "eu-west1", instances: 200, factor: 0.35 }
          ],
          samples: 1e3
        },
        reasoning: "Performing Monte Carlo analysis to compare emissions between regions"
      },
      {
        type: "final",
        response: `# Carbon Emission Comparison: ap-south1 vs eu-west1

## Summary
For 200 8-vCPU VM instances, eu-west1 has significantly lower carbon emissions than ap-south1.

## Results
- **ap-south1**: 164 ± 12 kg CO2e/day (95% CI: 152-176 kg)
- **eu-west1**: 70 ± 8 kg CO2e/day (95% CI: 62-78 kg)
- **Difference**: 94 kg CO2e/day (57% reduction with eu-west1)

## Recommendation
Choose eu-west1 for lower environmental impact. The carbon footprint is 57% lower due to cleaner electricity grid mix.

## Data Sources
- Carbon factors from Carbon Interface API
- Grid intensity from ElectricityMap
- Monte Carlo analysis with 1000 samples`,
        reasoning: "Provided comprehensive comparison with quantified results and clear recommendation"
      }
    ];
  }
  /**
   * Generate mock agent plan
   */
  async plan(conversationHistory, _options) {
    await delay(500 + Math.random() * 1e3);
    const responseIndex = Math.min(this.callCount, this.planResponses.length - 1);
    this.callCount++;
    const response = this.planResponses[responseIndex];
    if (!response) {
      return this.planResponses[this.planResponses.length - 1];
    }
    return { ...response };
  }
  /**
   * Generate mock summary
   */
  async summarize(text, _options) {
    await delay(300 + Math.random() * 500);
    const wordCount = text.split(" ").length;
    if (wordCount < 100) {
      return "This content discusses carbon emissions and environmental impact considerations for technology decisions.";
    } else if (wordCount < 500) {
      return `This ${wordCount}-word content covers carbon emission factors, regional differences in electricity grid intensity, and environmental impact assessment methodologies. Key topics include lifecycle analysis, renewable energy adoption, and sustainability metrics for technology infrastructure.`;
    } else {
      return `Comprehensive analysis of carbon emissions spanning ${wordCount} words. The content examines regional variations in carbon intensity, comparative lifecycle assessments, and decision frameworks for sustainable technology choices. Discusses grid decarbonization trends, emission factor databases, and Monte Carlo uncertainty analysis methods. Provides actionable insights for reducing environmental impact through informed technology and location decisions.`;
    }
  }
  /**
   * Stream mock agent plan
   */
  async streamPlan(conversationHistory, onDelta, options) {
    const plan = await this.plan(conversationHistory, options);
    const planText = JSON.stringify(plan, null, 2);
    for (let i = 0; i < planText.length; i += 3) {
      const chunk = planText.slice(i, i + 3);
      onDelta(chunk);
      await delay(50);
    }
  }
  /**
   * Mock configuration check
   */
  async isConfigured() {
    return true;
  }
  /**
   * Reset call count for testing
   */
  reset() {
    this.callCount = 0;
  }
  /**
   * Set custom plan responses for testing
   */
  setPlanResponses(responses) {
    this.planResponses = responses;
    this.callCount = 0;
  }
}
class BaseToolAdapter {
  /**
   * Basic argument validation against schema
   */
  validateArgs(args) {
    const required = this.schema.required || [];
    for (const field of required) {
      if (!(field in args) || args[field] === void 0 || args[field] === null) {
        return false;
      }
    }
    const properties = this.schema.properties || {};
    for (const [key, value] of Object.entries(args)) {
      const propSchema = properties[key];
      if (propSchema && propSchema.type) {
        const expectedType = propSchema.type;
        if (expectedType === "integer" && !Number.isInteger(value)) {
          return false;
        } else if (expectedType === "number" && typeof value !== "number") {
          return false;
        } else if (expectedType === "string" && typeof value !== "string") {
          return false;
        } else if (expectedType === "boolean" && typeof value !== "boolean") {
          return false;
        } else if (expectedType === "array" && !Array.isArray(value)) {
          return false;
        } else if (expectedType === "object" && (typeof value !== "object" || Array.isArray(value))) {
          return false;
        }
      }
    }
    return true;
  }
  /**
   * Create a successful tool result
   */
  createSuccessResult(data, metadata) {
    return {
      success: true,
      data,
      metadata: {
        executionTime: Date.now(),
        source: this.name,
        ...metadata
      }
    };
  }
  /**
   * Create an error tool result
   */
  createErrorResult(error, metadata) {
    return {
      success: false,
      error,
      metadata: {
        executionTime: Date.now(),
        source: this.name,
        ...metadata
      }
    };
  }
}
class ToolRegistry {
  constructor() {
    this.tools = /* @__PURE__ */ new Map();
  }
  /**
   * Register a tool adapter
   */
  register(tool) {
    this.tools.set(tool.name, tool);
  }
  /**
   * Get a tool by name
   */
  get(name) {
    return this.tools.get(name);
  }
  /**
   * Get all registered tools
   */
  getAll() {
    return Array.from(this.tools.values());
  }
  /**
   * Check if a tool is registered
   */
  has(name) {
    return this.tools.has(name);
  }
  /**
   * Execute a tool by name
   */
  async execute(name, args) {
    const tool = this.get(name);
    if (!tool) {
      return {
        success: false,
        error: `Tool '${name}' not found`,
        metadata: {
          executionTime: Date.now(),
          source: "ToolRegistry"
        }
      };
    }
    if (!tool.validateArgs(args)) {
      return {
        success: false,
        error: `Invalid arguments for tool '${name}'`,
        metadata: {
          executionTime: Date.now(),
          source: "ToolRegistry"
        }
      };
    }
    try {
      return await tool.execute(args);
    } catch (error) {
      return {
        success: false,
        error: `Tool execution failed: ${error.message}`,
        metadata: {
          executionTime: Date.now(),
          source: "ToolRegistry"
        }
      };
    }
  }
}
class CarbonApiTool extends BaseToolAdapter {
  constructor(backendUrl, apiKey, useMock = true) {
    super();
    this.backendUrl = backendUrl;
    this.apiKey = apiKey;
    this.useMock = useMock;
    this.name = "CarbonApiTool";
    this.description = "Query carbon emission factors from Carbon Interface or Climatiq APIs";
    this.schema = {
      type: "object",
      properties: {
        service: {
          type: "string",
          description: "Service type (compute, storage, network, etc.)",
          enum: ["compute", "storage", "network", "database", "serverless"]
        },
        region: {
          type: "string",
          description: "Cloud region or geographic location"
        },
        instanceType: {
          type: "string",
          description: "Instance or resource type"
        },
        provider: {
          type: "string",
          description: "Cloud provider (aws, gcp, azure, etc.)",
          enum: ["aws", "gcp", "azure", "alibaba", "generic"]
        }
      },
      required: ["service", "region"]
    };
  }
  /**
   * Execute carbon factor query
   */
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { service, region, instanceType, provider = "generic" } = args;
    try {
      if (this.useMock) {
        return this.getMockCarbonFactor(service, region, instanceType, provider);
      }
      if (this.backendUrl) {
        return await this.queryViaBackend(service, region, instanceType, provider);
      } else if (this.apiKey) {
        return await this.queryDirectly(service, region, instanceType, provider);
      } else {
        return this.createErrorResult("No API configuration available (backend URL or API key required)");
      }
    } catch (error) {
      return this.createErrorResult(`Carbon API query failed: ${error.message}`);
    }
  }
  /**
   * Query via backend proxy
   */
  async queryViaBackend(service, region, instanceType, provider) {
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/carbon/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ service, region, instanceType, provider })
      });
      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }
      return res.json();
    });
    return this.createSuccessResult(response.data, {
      source: "backend-proxy",
      cached: response.cached || false
    });
  }
  /**
   * Query API directly (not recommended for production)
   */
  async queryDirectly(service, region, instanceType, provider) {
    return this.createErrorResult(
      "Direct API calls not implemented for security reasons. Please use backend proxy."
    );
  }
  /**
   * Get mock carbon factor for testing
   */
  getMockCarbonFactor(service, region, instanceType, provider) {
    const regionFactors = {
      "us-east-1": 0.45,
      "us-west-2": 0.25,
      "eu-west-1": 0.35,
      "eu-central-1": 0.55,
      "ap-south-1": 0.82,
      "ap-southeast-1": 0.65,
      "ap-northeast-1": 0.48,
      "ca-central-1": 0.15,
      "sa-east-1": 0.12
    };
    const serviceMultipliers = {
      compute: 1,
      storage: 0.1,
      network: 0.05,
      database: 1.2,
      serverless: 0.8
    };
    const instanceMultipliers = {
      "1-vCPU": 0.5,
      "2-vCPU": 1,
      "4-vCPU": 2,
      "8-vCPU": 4,
      "16-vCPU": 8,
      "32-vCPU": 16
    };
    const baseFactor = regionFactors[region] || 0.5;
    const serviceMultiplier = serviceMultipliers[service] || 1;
    const instanceMultiplier = instanceMultipliers[instanceType] || 1;
    const factor = {
      value: baseFactor * serviceMultiplier * instanceMultiplier,
      unit: "kg CO2e/hour",
      source: "CarbonLens Mock Data",
      region,
      confidence: 0.85,
      updatedAt: Date.now()
    };
    return this.createSuccessResult(factor, {
      source: "mock",
      cached: false,
      query: { service, region, instanceType, provider }
    });
  }
}
class LCADatabaseTool extends BaseToolAdapter {
  constructor() {
    super(...arguments);
    this.name = "LCADatabaseTool";
    this.description = "Access curated lifecycle assessment data for offline comparisons";
    this.schema = {
      type: "object",
      properties: {
        category: {
          type: "string",
          description: "LCA category",
          enum: ["materials", "manufacturing", "transport", "energy", "waste"]
        },
        item: {
          type: "string",
          description: "Specific item or process"
        },
        unit: {
          type: "string",
          description: "Functional unit for comparison"
        }
      },
      required: ["category", "item"]
    };
    this.lcaData = {
      materials: {
        steel: [
          { value: 2.3, unit: "kg CO2e/kg", source: "Ecoinvent 3.8", confidence: 0.9, updatedAt: Date.now() }
        ],
        aluminum: [
          { value: 8.2, unit: "kg CO2e/kg", source: "Ecoinvent 3.8", confidence: 0.9, updatedAt: Date.now() }
        ],
        concrete: [
          { value: 0.35, unit: "kg CO2e/kg", source: "Ecoinvent 3.8", confidence: 0.85, updatedAt: Date.now() }
        ],
        silicon: [
          { value: 5.6, unit: "kg CO2e/kg", source: "Semiconductor LCA Study", confidence: 0.8, updatedAt: Date.now() }
        ]
      },
      manufacturing: {
        "cpu-chip": [
          { value: 25, unit: "kg CO2e/unit", source: "Intel LCA Report", confidence: 0.8, updatedAt: Date.now() }
        ],
        "memory-module": [
          { value: 8.5, unit: "kg CO2e/unit", source: "Samsung LCA Study", confidence: 0.75, updatedAt: Date.now() }
        ],
        "server-assembly": [
          { value: 1200, unit: "kg CO2e/unit", source: "Dell Server LCA", confidence: 0.8, updatedAt: Date.now() }
        ]
      },
      transport: {
        "air-freight": [
          { value: 1.02, unit: "kg CO2e/kg·km", source: "DEFRA 2023", confidence: 0.9, updatedAt: Date.now() }
        ],
        "sea-freight": [
          { value: 0.015, unit: "kg CO2e/kg·km", source: "IMO Study", confidence: 0.85, updatedAt: Date.now() }
        ],
        "truck-transport": [
          { value: 0.12, unit: "kg CO2e/kg·km", source: "EPA 2023", confidence: 0.9, updatedAt: Date.now() }
        ]
      },
      energy: {
        "grid-average-us": [
          { value: 0.45, unit: "kg CO2e/kWh", source: "EPA eGRID 2022", confidence: 0.95, updatedAt: Date.now() }
        ],
        "grid-average-eu": [
          { value: 0.35, unit: "kg CO2e/kWh", source: "EEA 2023", confidence: 0.95, updatedAt: Date.now() }
        ],
        "solar-pv": [
          { value: 0.048, unit: "kg CO2e/kWh", source: "IPCC AR6", confidence: 0.9, updatedAt: Date.now() }
        ],
        "wind-onshore": [
          { value: 0.011, unit: "kg CO2e/kWh", source: "IPCC AR6", confidence: 0.9, updatedAt: Date.now() }
        ]
      },
      waste: {
        "electronic-waste": [
          { value: 0.8, unit: "kg CO2e/kg", source: "E-waste LCA Study", confidence: 0.7, updatedAt: Date.now() }
        ],
        "landfill-general": [
          { value: 0.5, unit: "kg CO2e/kg", source: "EPA Waste LCA", confidence: 0.8, updatedAt: Date.now() }
        ]
      }
    };
  }
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { category, item, unit } = args;
    try {
      const categoryData = this.lcaData[category];
      if (!categoryData) {
        return this.createErrorResult(`Category '${category}' not found in LCA database`);
      }
      const itemData = categoryData[item.toLowerCase()];
      if (!itemData) {
        const availableItems = Object.keys(categoryData);
        return this.createErrorResult(
          `Item '${item}' not found in category '${category}'. Available items: ${availableItems.join(", ")}`
        );
      }
      let factors = itemData;
      if (unit) {
        factors = itemData.filter((factor) => factor.unit.includes(unit));
        if (factors.length === 0) {
          return this.createErrorResult(`No data found for unit '${unit}' in item '${item}'`);
        }
      }
      return this.createSuccessResult({
        category,
        item,
        factors,
        metadata: {
          totalFactors: factors.length,
          sources: [...new Set(factors.map((f) => f.source))],
          averageConfidence: factors.reduce((sum, f) => sum + (f.confidence || 0), 0) / factors.length
        }
      }, {
        source: "lca-database",
        cached: true
      });
    } catch (error) {
      return this.createErrorResult(`LCA database query failed: ${error.message}`);
    }
  }
}
class ElectricityIntensityTool extends BaseToolAdapter {
  constructor(backendUrl, apiKey, useMock = true) {
    super();
    this.backendUrl = backendUrl;
    this.apiKey = apiKey;
    this.useMock = useMock;
    this.name = "ElectricityIntensityTool";
    this.description = "Get regional electricity grid carbon intensity data";
    this.schema = {
      type: "object",
      properties: {
        region: {
          type: "string",
          description: "Region code or name (e.g., UK, DE, US-CA, etc.)"
        },
        forecast: {
          type: "boolean",
          description: "Whether to include forecast data",
          default: false
        },
        hours: {
          type: "integer",
          description: "Number of hours of data to retrieve",
          minimum: 1,
          maximum: 168,
          default: 24
        }
      },
      required: ["region"]
    };
  }
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { region, forecast = false, hours = 24 } = args;
    try {
      if (this.useMock) {
        return this.getMockGridIntensity(region, forecast, hours);
      }
      if (this.backendUrl) {
        return await this.queryViaBackend(region, forecast, hours);
      } else {
        return this.createErrorResult("No backend URL configured for electricity intensity data");
      }
    } catch (error) {
      return this.createErrorResult(`Electricity intensity query failed: ${error.message}`);
    }
  }
  async queryViaBackend(region, forecast, hours) {
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/electricity/intensity`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region, forecast, hours })
      });
      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }
      return res.json();
    });
    return this.createSuccessResult(response.data, {
      source: "backend-proxy",
      cached: response.cached || false
    });
  }
  getMockGridIntensity(region, forecast, hours) {
    const regionIntensities = {
      "UK": { base: 180, renewable: 45 },
      "DE": { base: 350, renewable: 55 },
      "FR": { base: 60, renewable: 85 },
      "US-CA": { base: 250, renewable: 35 },
      "US-TX": { base: 450, renewable: 25 },
      "NO": { base: 20, renewable: 98 },
      "PL": { base: 650, renewable: 15 },
      "IN": { base: 820, renewable: 12 },
      "CN": { base: 550, renewable: 28 },
      "AU": { base: 480, renewable: 32 }
    };
    const regionData = regionIntensities[region.toUpperCase()] || { base: 400, renewable: 30 };
    const currentTime = Date.now();
    const data = [];
    for (let i = 0; i < hours; i++) {
      const hour = new Date(currentTime + i * 36e5).getHours();
      const dailyMultiplier = 0.7 + 0.6 * Math.sin((hour - 6) * Math.PI / 12);
      const randomVariation = 0.9 + 0.2 * Math.random();
      const intensity = Math.round(regionData.base * dailyMultiplier * randomVariation);
      data.push({
        region,
        intensity,
        renewablePercent: regionData.renewable + (Math.random() - 0.5) * 10,
        timestamp: currentTime + i * 36e5,
        source: "CarbonLens Mock Grid Data"
      });
    }
    if (forecast) {
      for (let i = hours; i < hours + 24; i++) {
        const hour = new Date(currentTime + i * 36e5).getHours();
        const dailyMultiplier = 0.7 + 0.6 * Math.sin((hour - 6) * Math.PI / 12);
        const randomVariation = 0.9 + 0.2 * Math.random();
        const intensity = Math.round(regionData.base * dailyMultiplier * randomVariation);
        data.push({
          region,
          intensity,
          renewablePercent: regionData.renewable + (Math.random() - 0.5) * 10,
          timestamp: currentTime + i * 36e5,
          source: "CarbonLens Mock Grid Forecast"
        });
      }
    }
    const avgIntensity = data.reduce((sum, d) => sum + d.intensity, 0) / data.length;
    const avgRenewable = data.reduce((sum, d) => sum + (d.renewablePercent || 0), 0) / data.length;
    return this.createSuccessResult({
      region,
      data,
      summary: {
        averageIntensity: Math.round(avgIntensity),
        averageRenewable: Math.round(avgRenewable),
        minIntensity: Math.min(...data.map((d) => d.intensity)),
        maxIntensity: Math.max(...data.map((d) => d.intensity)),
        dataPoints: data.length
      }
    }, {
      source: "mock",
      cached: false,
      forecast,
      hours: data.length
    });
  }
}
class NewsSearchTool extends BaseToolAdapter {
  constructor(backendUrl, apiKey, useMock = true) {
    super();
    this.backendUrl = backendUrl;
    this.apiKey = apiKey;
    this.useMock = useMock;
    this.name = "NewsSearchTool";
    this.description = "Search for recent carbon/climate news and reports";
    this.schema = {
      type: "object",
      properties: {
        query: {
          type: "string",
          description: "Search query for news articles"
        },
        category: {
          type: "string",
          description: "News category filter",
          enum: ["carbon", "climate", "renewable", "emissions", "sustainability", "policy"]
        },
        days: {
          type: "integer",
          description: "Number of days to look back",
          minimum: 1,
          maximum: 30,
          default: 7
        },
        limit: {
          type: "integer",
          description: "Maximum number of articles to return",
          minimum: 1,
          maximum: 50,
          default: 10
        }
      },
      required: ["query"]
    };
  }
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { query, category, days = 7, limit = 10 } = args;
    try {
      if (this.useMock) {
        return this.getMockNews(query, category, days, limit);
      }
      if (this.backendUrl) {
        return await this.queryViaBackend(query, category, days, limit);
      } else {
        return this.createErrorResult("No backend URL configured for news search");
      }
    } catch (error) {
      return this.createErrorResult(`News search failed: ${error.message}`);
    }
  }
  async queryViaBackend(query, category, days, limit) {
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/news/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, category, days, limit })
      });
      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }
      return res.json();
    });
    return this.createSuccessResult(response.data, {
      source: "backend-proxy",
      cached: response.cached || false
    });
  }
  getMockNews(query, category, days, limit) {
    const mockArticles = [
      {
        title: "Major Cloud Providers Announce Carbon Neutral Commitments for 2030",
        description: "Leading cloud computing companies have pledged to achieve carbon neutrality across their global operations by 2030, with significant investments in renewable energy and carbon offset programs.",
        url: "https://example.com/cloud-carbon-neutral-2030",
        source: "Tech Climate News",
        publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1e3).toISOString(),
        relevanceScore: 0.95
      },
      {
        title: "New Study Reveals Regional Variations in Data Center Carbon Intensity",
        description: "Research shows significant differences in carbon emissions per compute unit across global regions, with Nordic countries showing 80% lower emissions than coal-dependent regions.",
        url: "https://example.com/datacenter-regional-carbon-study",
        source: "Environmental Computing Journal",
        publishedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1e3).toISOString(),
        relevanceScore: 0.92
      },
      {
        title: "EU Introduces Mandatory Carbon Reporting for Digital Services",
        description: "New regulations require all digital service providers in the EU to report their carbon footprint and implement reduction strategies by 2025.",
        url: "https://example.com/eu-digital-carbon-reporting",
        source: "EU Policy Watch",
        publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1e3).toISOString(),
        relevanceScore: 0.88
      },
      {
        title: "Breakthrough in Green Hydrogen Production Could Transform Energy Storage",
        description: "Scientists develop new catalyst that reduces energy requirements for hydrogen production by 40%, potentially revolutionizing renewable energy storage.",
        url: "https://example.com/green-hydrogen-breakthrough",
        source: "Renewable Energy Today",
        publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1e3).toISOString(),
        relevanceScore: 0.85
      },
      {
        title: "Carbon Pricing Mechanisms Show Effectiveness in Reducing Industrial Emissions",
        description: "Analysis of global carbon pricing systems demonstrates average 15% reduction in industrial emissions where implemented.",
        url: "https://example.com/carbon-pricing-effectiveness",
        source: "Climate Policy Review",
        publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1e3).toISOString(),
        relevanceScore: 0.82
      }
    ];
    let filteredArticles = mockArticles.filter((article) => {
      const queryMatch = article.title.toLowerCase().includes(query.toLowerCase()) || article.description.toLowerCase().includes(query.toLowerCase());
      const categoryMatch = !category || article.title.toLowerCase().includes(category.toLowerCase()) || article.description.toLowerCase().includes(category.toLowerCase());
      const dateMatch = new Date(article.publishedAt) >= new Date(Date.now() - days * 24 * 60 * 60 * 1e3);
      return queryMatch && categoryMatch && dateMatch;
    });
    filteredArticles = filteredArticles.sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0)).slice(0, limit);
    return this.createSuccessResult({
      articles: filteredArticles,
      query,
      category,
      totalResults: filteredArticles.length,
      searchParameters: { query, category, days, limit }
    }, {
      source: "mock",
      cached: false,
      resultsFound: filteredArticles.length
    });
  }
}
class EmissionEstimatorTool extends BaseToolAdapter {
  constructor() {
    super(...arguments);
    this.name = "EmissionEstimatorTool";
    this.description = "Perform Monte Carlo emission calculations with uncertainty analysis";
    this.schema = {
      type: "object",
      properties: {
        scenarios: {
          type: "array",
          description: "Array of emission scenarios to analyze",
          items: {
            type: "object",
            properties: {
              name: { type: "string", description: "Scenario identifier" },
              instances: { type: "integer", description: "Number of instances/units", minimum: 1 },
              factor: { type: "number", description: "Carbon factor (kg CO2e/unit/hour)", minimum: 0 },
              hoursPerDay: { type: "number", description: "Usage hours per day", minimum: 0, maximum: 24 },
              uncertainty: { type: "number", description: "Uncertainty as fraction (0-1)", minimum: 0, maximum: 1 }
            },
            required: ["instances", "factor"]
          }
        },
        samples: {
          type: "integer",
          description: "Number of Monte Carlo samples",
          minimum: 100,
          maximum: 1e5,
          default: 1e4
        },
        timeframe: {
          type: "string",
          description: "Timeframe for calculation",
          enum: ["hour", "day", "week", "month", "year"],
          default: "day"
        }
      },
      required: ["scenarios"]
    };
  }
  /**
   * Execute emission estimation
   */
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { scenarios, samples = 1e4, timeframe = "day" } = args;
    try {
      const results = {};
      for (const scenario of scenarios) {
        const estimate = this.calculateEmissions(scenario, samples, timeframe);
        const scenarioName = scenario.name || `Scenario ${Object.keys(results).length + 1}`;
        results[scenarioName] = estimate;
      }
      const comparison = scenarios.length > 1 ? this.calculateComparison(results) : null;
      return this.createSuccessResult({
        estimates: results,
        comparison,
        parameters: { samples, timeframe }
      }, {
        samples,
        scenarios: scenarios.length
      });
    } catch (error) {
      return this.createErrorResult(`Emission calculation failed: ${error.message}`);
    }
  }
  /**
   * Calculate emissions for a single scenario using Monte Carlo
   */
  calculateEmissions(scenario, samples, timeframe) {
    const { instances, factor, hoursPerDay = 24, uncertainty = 0.1 } = scenario;
    const timeMultipliers = {
      hour: 1,
      day: hoursPerDay,
      week: hoursPerDay * 7,
      month: hoursPerDay * 30,
      year: hoursPerDay * 365
    };
    const timeMultiplier = timeMultipliers[timeframe] || hoursPerDay;
    const emissions = [];
    const breakdown = {
      compute: [],
      uncertainty: []
    };
    for (let i = 0; i < samples; i++) {
      const factorSample = this.sampleLogNormal(factor, factor * uncertainty);
      const emission = instances * factorSample * timeMultiplier;
      emissions.push(emission);
      breakdown.compute?.push(emission);
      breakdown.uncertainty?.push(Math.abs(emission - instances * factor * timeMultiplier));
    }
    const mean = emissions.reduce((sum, val) => sum + val, 0) / samples;
    const variance = emissions.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (samples - 1);
    const std = Math.sqrt(variance);
    const confidenceInterval = calculateConfidenceInterval(mean, std);
    const breakdownMeans = {};
    for (const [key, values] of Object.entries(breakdown)) {
      breakdownMeans[key] = values.reduce((sum, val) => sum + val, 0) / samples;
    }
    return {
      mean,
      std,
      unit: `kg CO2e/${timeframe}`,
      confidenceInterval,
      breakdown: breakdownMeans,
      samples
    };
  }
  /**
   * Sample from log-normal distribution
   */
  sampleLogNormal(mean, std) {
    const u1 = Math.random();
    const u2 = Math.random();
    const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    const logMean = Math.log(mean) - 0.5 * Math.log(1 + (std / mean) ** 2);
    const logStd = Math.sqrt(Math.log(1 + (std / mean) ** 2));
    return Math.exp(logMean + logStd * z0);
  }
  /**
   * Calculate comparison metrics between scenarios
   */
  calculateComparison(results) {
    const scenarios = Object.keys(results);
    if (scenarios.length < 2) return null;
    const comparisons = {};
    for (let i = 0; i < scenarios.length; i++) {
      for (let j = i + 1; j < scenarios.length; j++) {
        const scenario1 = scenarios[i];
        const scenario2 = scenarios[j];
        const result1 = results[scenario1];
        const result2 = results[scenario2];
        if (!result1 || !result2) continue;
        const difference = result2.mean - result1.mean;
        const percentChange = difference / result1.mean * 100;
        comparisons[`${scenario1}_vs_${scenario2}`] = {
          difference,
          percentChange,
          unit: result1.unit,
          lowerEmission: difference < 0 ? scenario2 : scenario1,
          reduction: Math.abs(percentChange)
        };
      }
    }
    const sortedScenarios = scenarios.sort((a, b) => results[a].mean - results[b].mean);
    return {
      pairwise: comparisons,
      ranking: {
        best: sortedScenarios[0],
        worst: sortedScenarios[sortedScenarios.length - 1],
        order: sortedScenarios
      },
      totalRange: {
        min: results[sortedScenarios[0]].mean,
        max: results[sortedScenarios[sortedScenarios.length - 1]].mean,
        span: results[sortedScenarios[sortedScenarios.length - 1]].mean - results[sortedScenarios[0]].mean
      }
    };
  }
}
class NotifierTool extends BaseToolAdapter {
  constructor(backendUrl, channels = [], useMock = true) {
    super();
    this.backendUrl = backendUrl;
    this.channels = channels;
    this.useMock = useMock;
    this.name = "NotifierTool";
    this.description = "Send notifications via configured channels (Slack, Telegram, Email)";
    this.schema = {
      type: "object",
      properties: {
        message: {
          type: "string",
          description: "Notification message content"
        },
        title: {
          type: "string",
          description: "Notification title/subject"
        },
        channel: {
          type: "string",
          description: "Notification channel name or type"
        },
        priority: {
          type: "string",
          description: "Notification priority level",
          enum: ["low", "normal", "high", "urgent"],
          default: "normal"
        },
        data: {
          type: "object",
          description: "Additional structured data to include"
        }
      },
      required: ["message"]
    };
  }
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { message, title, channel, priority = "normal", data } = args;
    try {
      if (this.useMock) {
        return this.getMockNotification(message, title, channel, priority, data);
      }
      if (this.backendUrl) {
        return await this.sendViaBackend(message, title, channel, priority, data);
      } else {
        return this.createErrorResult("No backend URL configured for notifications");
      }
    } catch (error) {
      return this.createErrorResult(`Notification failed: ${error.message}`);
    }
  }
  async sendViaBackend(message, title, channel, priority, data) {
    const payload = {
      message,
      title,
      channel,
      priority,
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
    const response = await retryWithBackoff(async () => {
      const res = await fetch(`${this.backendUrl}/api/notify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        throw new Error(`Backend API error: ${res.status} ${res.statusText}`);
      }
      return res.json();
    });
    return this.createSuccessResult(response.data, {
      source: "backend-proxy",
      deliveryStatus: response.status || "sent"
    });
  }
  getMockNotification(message, title, channel, priority, data) {
    const selectedChannel = channel || "default";
    const deliverySuccess = Math.random() > 0.05;
    const deliveryTime = Math.floor(Math.random() * 2e3) + 500;
    if (!deliverySuccess) {
      return this.createErrorResult("Mock notification delivery failed (simulated network error)");
    }
    const notification = {
      id: `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      message,
      title: title || "CarbonLens Notification",
      channel: selectedChannel,
      priority,
      data,
      timestamp: (/* @__PURE__ */ new Date()).toISOString(),
      deliveryTime,
      status: "delivered"
    };
    let formattedMessage = message;
    if (selectedChannel.includes("slack")) {
      formattedMessage = this.formatSlackMessage(message, title, data);
    } else if (selectedChannel.includes("telegram")) {
      formattedMessage = this.formatTelegramMessage(message, title, data);
    } else if (selectedChannel.includes("email")) {
      formattedMessage = this.formatEmailMessage(message, title, data);
    }
    return this.createSuccessResult({
      notification,
      formattedMessage,
      deliveryConfirmation: {
        delivered: true,
        deliveryTime,
        channel: selectedChannel,
        messageId: notification.id
      }
    }, {
      source: "mock",
      deliveryTime,
      channel: selectedChannel
    });
  }
  formatSlackMessage(message, title, data) {
    const blocks = [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: title || "CarbonLens Alert"
        }
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: message
        }
      }
    ];
    if (data) {
      blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: `\`\`\`${JSON.stringify(data, null, 2)}\`\`\``
        }
      });
    }
    return JSON.stringify({ blocks }, null, 2);
  }
  formatTelegramMessage(message, title, data) {
    let formatted = `*${title || "CarbonLens Alert"}*

${message}`;
    if (data) {
      formatted += `

\`\`\`json
${JSON.stringify(data, null, 2)}
\`\`\``;
    }
    return formatted;
  }
  formatEmailMessage(message, title, data) {
    let html = `
      <html>
        <body>
          <h2>${title || "CarbonLens Alert"}</h2>
          <p>${message}</p>
    `;
    if (data) {
      html += `
          <h3>Additional Data:</h3>
          <pre>${JSON.stringify(data, null, 2)}</pre>
      `;
    }
    html += `
        </body>
      </html>
    `;
    return html;
  }
}
class PageExtractorTool extends BaseToolAdapter {
  constructor() {
    super(...arguments);
    this.name = "PageExtractorTool";
    this.description = "Extract structured product/spec info from current webpage";
    this.schema = {
      type: "object",
      properties: {
        url: {
          type: "string",
          description: "URL to extract data from (optional, uses current page if not provided)"
        },
        extractTypes: {
          type: "array",
          description: "Types of data to extract",
          items: {
            type: "string",
            enum: ["specs", "energy", "location", "pricing", "all"]
          },
          default: ["all"]
        }
      }
    };
  }
  async execute(args) {
    if (!this.validateArgs(args)) {
      return this.createErrorResult("Invalid arguments provided");
    }
    const { url, extractTypes = ["all"] } = args;
    try {
      const extraction = await this.extractPageData(url, extractTypes);
      return this.createSuccessResult(extraction, {
        source: "page-extractor",
        extractionTime: Date.now(),
        extractTypes
      });
    } catch (error) {
      return this.createErrorResult(`Page extraction failed: ${error.message}`);
    }
  }
  async extractPageData(url, extractTypes = ["all"]) {
    const currentUrl = url || "https://example.com/cloud-instance-specs";
    const currentTitle = "High-Performance Cloud Computing Instances";
    const extraction = {
      url: currentUrl,
      title: currentTitle,
      data: {}
    };
    if (extractTypes.includes("all") || extractTypes.includes("specs")) {
      extraction.data.specs = this.extractSpecs(currentUrl);
    }
    if (extractTypes.includes("all") || extractTypes.includes("energy")) {
      extraction.data.energy = this.extractEnergyInfo(currentUrl);
    }
    if (extractTypes.includes("all") || extractTypes.includes("location")) {
      extraction.data.location = this.extractLocationInfo(currentUrl);
    }
    if (extractTypes.includes("all") || extractTypes.includes("pricing")) {
      extraction.data.pricing = this.extractPricingInfo(currentUrl);
    }
    return extraction;
  }
  extractSpecs(url) {
    if (url.includes("aws") || url.includes("ec2")) {
      return {
        instanceType: "m5.2xlarge",
        vCPUs: 8,
        memory: "32 GiB",
        storage: "EBS-optimized",
        network: "Up to 10 Gbps",
        architecture: "x86_64"
      };
    } else if (url.includes("gcp") || url.includes("compute")) {
      return {
        machineType: "n2-standard-8",
        vCPUs: 8,
        memory: "32 GB",
        storage: "Persistent SSD",
        network: "16 Gbps",
        architecture: "x86_64"
      };
    } else if (url.includes("azure")) {
      return {
        vmSize: "Standard_D8s_v3",
        vCPUs: 8,
        memory: "32 GiB",
        storage: "Premium SSD",
        network: "Moderate to High",
        architecture: "x86_64"
      };
    } else {
      return {
        instanceType: "Standard 8-vCPU",
        vCPUs: 8,
        memory: "32 GB",
        storage: "SSD",
        network: "High-speed",
        architecture: "x86_64"
      };
    }
  }
  extractEnergyInfo(url) {
    const baseConsumption = 150;
    const variation = Math.random() * 50 - 25;
    return {
      power: Math.round(baseConsumption + variation),
      powerUnit: "watts",
      efficiency: "Energy Star certified",
      powerUsageEffectiveness: 1.2 + Math.random() * 0.3
      // PUE between 1.2-1.5
    };
  }
  extractLocationInfo(url) {
    const regions = [
      { region: "us-east-1", country: "United States", datacenter: "Virginia" },
      { region: "eu-west-1", country: "Ireland", datacenter: "Dublin" },
      { region: "ap-south-1", country: "India", datacenter: "Mumbai" },
      { region: "ap-southeast-1", country: "Singapore", datacenter: "Singapore" }
    ];
    if (url.includes("us-east")) {
      return regions[0];
    } else if (url.includes("eu-west")) {
      return regions[1];
    } else if (url.includes("ap-south")) {
      return regions[2];
    } else if (url.includes("ap-southeast")) {
      return regions[3];
    } else {
      return regions[Math.floor(Math.random() * regions.length)];
    }
  }
  extractPricingInfo(url) {
    const baseCost = 0.096;
    const variation = Math.random() * 0.04 - 0.02;
    return {
      cost: Math.round((baseCost + variation) * 1e3) / 1e3,
      currency: "USD",
      period: "hour",
      billingModel: "on-demand",
      reservedInstanceDiscount: "30-60%"
    };
  }
}
class AgentOrchestrator {
  constructor(geminiService, toolRegistry, conversationStorage) {
    this.geminiService = geminiService;
    this.toolRegistry = toolRegistry;
    this.conversationStorage = conversationStorage;
    this.maxSteps = 20;
    this.maxRetries = 3;
  }
  /**
   * Run a task with streaming updates
   */
  async runTask(taskRequest, onDelta) {
    const taskId = generateId();
    const startTime = Date.now();
    let totalSteps = 0;
    let llmCalls = 0;
    let toolCalls = 0;
    try {
      await this.logEvent(taskId, "user_prompt", taskRequest.prompt);
      const conversationHistory = [
        `User Request: ${taskRequest.prompt}`,
        `Task Parameters: ${JSON.stringify({
          samples: taskRequest.samples,
          useBackend: taskRequest.useBackend,
          notifyChannel: taskRequest.notifyChannel?.name
        })}`
      ];
      this.emitDelta(onDelta, "plan", "Starting task analysis...");
      while (totalSteps < this.maxSteps) {
        totalSteps++;
        this.emitDelta(onDelta, "plan", `Step ${totalSteps}: Analyzing next action...`);
        const plan = await retryWithBackoff(async () => {
          llmCalls++;
          return await this.geminiService.plan(conversationHistory);
        }, this.maxRetries);
        await this.logEvent(taskId, "llm_plan", plan);
        if (plan.type === "final") {
          this.emitDelta(onDelta, "final", plan.response || "Task completed");
          await this.logEvent(taskId, "final", {
            response: plan.response,
            reasoning: plan.reasoning
          });
          if (taskRequest.notifyChannel) {
            await this.sendNotification(taskRequest, plan.response || "Task completed");
          }
          return {
            taskId,
            success: true,
            result: {
              response: plan.response,
              reasoning: plan.reasoning,
              conversationHistory
            },
            metadata: {
              startTime,
              endTime: Date.now(),
              totalSteps,
              llmCalls,
              toolCalls
            }
          };
        }
        if (plan.type === "tool_call" && plan.tool && plan.args) {
          this.emitDelta(onDelta, "tool_call", `Executing ${plan.tool}...`);
          await this.logEvent(taskId, "tool_call", {
            tool: plan.tool,
            args: plan.args,
            reasoning: plan.reasoning
          });
          const toolResult = await retryWithBackoff(async () => {
            toolCalls++;
            return await this.toolRegistry.execute(plan.tool, plan.args);
          }, this.maxRetries);
          await this.logEvent(taskId, "tool_result", toolResult);
          this.emitDelta(
            onDelta,
            "tool_result",
            toolResult.success ? "Tool execution completed" : `Tool error: ${toolResult.error}`
          );
          conversationHistory.push(
            `Tool Call: ${plan.tool}(${JSON.stringify(plan.args)})`,
            `Tool Result: ${JSON.stringify(toolResult, null, 2)}`
          );
          if (!toolResult.success) {
            conversationHistory.push(
              `Note: The tool call failed with error: ${toolResult.error}. Please try a different approach or tool.`
            );
          }
        } else {
          conversationHistory.push(
            "Error: Invalid plan format received. Please respond with valid JSON in the specified format."
          );
          this.emitDelta(onDelta, "plan", "Requesting proper JSON format...");
        }
      }
      const errorMessage = `Task exceeded maximum steps (${this.maxSteps}) without completion`;
      await this.logEvent(taskId, "final", { error: errorMessage });
      return {
        taskId,
        success: false,
        error: errorMessage,
        metadata: {
          startTime,
          endTime: Date.now(),
          totalSteps,
          llmCalls,
          toolCalls
        }
      };
    } catch (error) {
      const errorMessage = `Task execution failed: ${error.message}`;
      await this.logEvent(taskId, "final", { error: errorMessage });
      this.emitDelta(onDelta, "error", errorMessage);
      return {
        taskId,
        success: false,
        error: errorMessage,
        metadata: {
          startTime,
          endTime: Date.now(),
          totalSteps,
          llmCalls,
          toolCalls
        }
      };
    }
  }
  /**
   * Log conversation event
   */
  async logEvent(taskId, type, data) {
    const event = {
      id: generateId(),
      taskId,
      type,
      timestamp: Date.now(),
      data
    };
    await this.conversationStorage.addEvent(event);
  }
  /**
   * Emit streaming delta
   */
  emitDelta(onDelta, type, content, data) {
    if (onDelta) {
      onDelta({ type, content, data });
    }
  }
  /**
   * Send notification if configured
   */
  async sendNotification(taskRequest, result) {
    if (!taskRequest.notifyChannel) return;
    try {
      const notifierTool = this.toolRegistry.get("NotifierTool");
      if (notifierTool) {
        await notifierTool.execute({
          message: `CarbonLens task completed: ${result.substring(0, 200)}...`,
          title: "CarbonLens Task Complete",
          channel: taskRequest.notifyChannel.name,
          priority: "normal",
          data: {
            taskPrompt: taskRequest.prompt,
            completedAt: (/* @__PURE__ */ new Date()).toISOString()
          }
        });
      }
    } catch (error) {
      console.error("Failed to send notification:", error);
    }
  }
  /**
   * Get task conversation history
   */
  async getTaskHistory(taskId) {
    return await this.conversationStorage.getEvents(taskId);
  }
  /**
   * Export task logs
   */
  async exportTaskLogs(taskId) {
    return await this.conversationStorage.exportLogs(taskId);
  }
}
class ChromeConversationStorage {
  constructor() {
    this.STORAGE_KEY = "carbonlens_conversations";
    this.MAX_EVENTS = 1e4;
  }
  // Limit storage size
  /**
   * Add conversation event
   */
  async addEvent(event) {
    return new Promise((resolve, reject) => {
      chrome.storage.local.get([this.STORAGE_KEY], (result) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        const events = result[this.STORAGE_KEY] || [];
        events.push(event);
        if (events.length > this.MAX_EVENTS) {
          events.splice(0, events.length - this.MAX_EVENTS);
        }
        chrome.storage.local.set({ [this.STORAGE_KEY]: events }, () => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve();
          }
        });
      });
    });
  }
  /**
   * Get events for a specific task
   */
  async getEvents(taskId) {
    return new Promise((resolve, reject) => {
      chrome.storage.local.get([this.STORAGE_KEY], (result) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        const events = result[this.STORAGE_KEY] || [];
        const taskEvents = events.filter((event) => event.taskId === taskId);
        resolve(taskEvents.sort((a, b) => a.timestamp - b.timestamp));
      });
    });
  }
  /**
   * Export logs for a task as formatted text
   */
  async exportLogs(taskId) {
    const events = await this.getEvents(taskId);
    let logText = `CarbonLens Task Log - ${taskId}
`;
    logText += `Generated: ${(/* @__PURE__ */ new Date()).toISOString()}
`;
    logText += "=".repeat(80) + "\n\n";
    for (const event of events) {
      const timestamp = new Date(event.timestamp).toISOString();
      logText += `[${timestamp}] ${event.type.toUpperCase()}
`;
      if (typeof event.data === "string") {
        logText += `${event.data}
`;
      } else {
        logText += `${JSON.stringify(event.data, null, 2)}
`;
      }
      logText += "-".repeat(40) + "\n";
    }
    return logText;
  }
  /**
   * Clear all conversation data
   */
  async clearAll() {
    return new Promise((resolve, reject) => {
      chrome.storage.local.remove([this.STORAGE_KEY], () => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve();
        }
      });
    });
  }
}
class AgentRunner {
  constructor(geminiService, toolRegistry) {
    this.geminiService = geminiService;
    this.toolRegistry = toolRegistry;
    this.activeTasks = /* @__PURE__ */ new Map();
    this.conversationStorage = new ChromeConversationStorage();
  }
  /**
   * Start a new task
   */
  async startTask(request, onDelta) {
    const taskId = generateId();
    const orchestrator = new AgentOrchestrator(
      this.geminiService,
      this.toolRegistry,
      this.conversationStorage
    );
    const context = {
      taskId,
      request,
      orchestrator,
      startTime: Date.now(),
      status: "running",
      onDelta
    };
    this.activeTasks.set(taskId, context);
    this.executeTask(context).catch((error) => {
      console.error(`Task ${taskId} failed:`, error);
      context.status = "failed";
      context.result = {
        taskId,
        success: false,
        error: error.message,
        metadata: {
          startTime: context.startTime,
          endTime: Date.now(),
          totalSteps: 0,
          llmCalls: 0,
          toolCalls: 0
        }
      };
    });
    return taskId;
  }
  /**
   * Execute task in background
   */
  async executeTask(context) {
    try {
      const result = await context.orchestrator.runTask(context.request, context.onDelta);
      context.result = result;
      context.status = result.success ? "completed" : "failed";
      if (context.onDelta) {
        context.onDelta({
          type: "final",
          content: result.success ? "Task completed successfully" : `Task failed: ${result.error}`,
          data: result
        });
      }
    } catch (error) {
      context.status = "failed";
      context.result = {
        taskId: context.taskId,
        success: false,
        error: error.message,
        metadata: {
          startTime: context.startTime,
          endTime: Date.now(),
          totalSteps: 0,
          llmCalls: 0,
          toolCalls: 0
        }
      };
      if (context.onDelta) {
        context.onDelta({
          type: "error",
          content: `Task execution failed: ${error.message}`
        });
      }
    }
  }
  /**
   * Get task status
   */
  getTaskStatus(taskId) {
    return this.activeTasks.get(taskId);
  }
  /**
   * Get task result
   */
  getTaskResult(taskId) {
    const context = this.activeTasks.get(taskId);
    return context?.result;
  }
  /**
   * Cancel a running task
   */
  cancelTask(taskId) {
    const context = this.activeTasks.get(taskId);
    if (context && context.status === "running") {
      context.status = "cancelled";
      return true;
    }
    return false;
  }
  /**
   * Get all active tasks
   */
  getActiveTasks() {
    return Array.from(this.activeTasks.values()).filter((ctx) => ctx.status === "running");
  }
  /**
   * Clean up completed tasks
   */
  cleanupCompletedTasks() {
    const cutoffTime = Date.now() - 24 * 60 * 60 * 1e3;
    for (const [taskId, context] of this.activeTasks.entries()) {
      if (context.status !== "running" && context.startTime < cutoffTime) {
        this.activeTasks.delete(taskId);
      }
    }
  }
  /**
   * Export task logs
   */
  async exportTaskLogs(taskId) {
    return await this.conversationStorage.exportLogs(taskId);
  }
  /**
   * Get task conversation history
   */
  async getTaskHistory(taskId) {
    return await this.conversationStorage.getEvents(taskId);
  }
}
function buildContainer(config) {
  const geminiService = config.useRealMode && config.apiKeys?.gemini ? new GeminiService(config.apiKeys.gemini) : new GeminiMock();
  const toolRegistry = new ToolRegistry();
  toolRegistry.register(new CarbonApiTool(
    config.backendUrl,
    config.apiKeys?.carbonInterface,
    !config.useRealMode
  ));
  toolRegistry.register(new LCADatabaseTool());
  toolRegistry.register(new ElectricityIntensityTool(
    config.backendUrl,
    config.apiKeys?.electricityMap,
    !config.useRealMode
  ));
  toolRegistry.register(new NewsSearchTool(
    config.backendUrl,
    config.apiKeys?.newsApi,
    !config.useRealMode
  ));
  toolRegistry.register(new EmissionEstimatorTool());
  toolRegistry.register(new NotifierTool(
    config.backendUrl,
    config.notificationChannels,
    !config.useRealMode
  ));
  toolRegistry.register(new PageExtractorTool());
  const agentRunner = new AgentRunner(geminiService, toolRegistry);
  return {
    geminiService,
    toolRegistry,
    agentRunner
  };
}
let container;
initializeContainer();
async function initializeContainer() {
  try {
    const config = await getExtensionConfig();
    container = buildContainer(config);
    console.log("CarbonLens service worker initialized");
  } catch (error) {
    console.error("Failed to initialize service worker:", error);
    container = buildContainer({
      useRealMode: false,
      notificationChannels: []
    });
  }
}
async function getExtensionConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["carbonlens_config"], (result) => {
      const config = result.carbonlens_config || {
        useRealMode: false,
        notificationChannels: []
      };
      resolve(config);
    });
  });
}
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    try {
      switch (message.action) {
        case "startTask":
          const taskRequest = message.taskRequest;
          const taskId = await container.agentRunner.startTask(taskRequest);
          sendResponse({ success: true, taskId });
          break;
        case "getTaskStatus":
          const status = container.agentRunner.getTaskStatus(message.taskId);
          sendResponse({ success: true, status });
          break;
        case "getTaskResult":
          const result = container.agentRunner.getTaskResult(message.taskId);
          sendResponse({ success: true, result });
          break;
        case "cancelTask":
          const cancelled = container.agentRunner.cancelTask(message.taskId);
          sendResponse({ success: true, cancelled });
          break;
        case "exportTaskLogs":
          const logs = await container.agentRunner.exportTaskLogs(message.taskId);
          sendResponse({ success: true, logs });
          break;
        case "getTaskHistory":
          const history = await container.agentRunner.getTaskHistory(message.taskId);
          sendResponse({ success: true, history });
          break;
        case "updateConfig":
          const newConfig = message.config;
          await saveExtensionConfig(newConfig);
          container = buildContainer(newConfig);
          sendResponse({ success: true });
          break;
        case "getConfig":
          const currentConfig = await getExtensionConfig();
          sendResponse({ success: true, config: currentConfig });
          break;
        case "getActiveTasks":
          const activeTasks = container.agentRunner.getActiveTasks();
          sendResponse({ success: true, tasks: activeTasks });
          break;
        default:
          sendResponse({ success: false, error: "Unknown action" });
      }
    } catch (error) {
      console.error("Service worker message handler error:", error);
      sendResponse({ success: false, error: error.message });
    }
  })();
  return true;
});
chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "carbonlens-stream") {
    port.onMessage.addListener(async (message) => {
      if (message.action === "startStreamingTask") {
        try {
          const taskRequest = message.taskRequest;
          const taskId = await container.agentRunner.startTask(
            taskRequest,
            (delta) => {
              port.postMessage({
                type: "delta",
                taskId,
                delta
              });
            }
          );
          port.postMessage({
            type: "started",
            taskId
          });
        } catch (error) {
          port.postMessage({
            type: "error",
            error: error.message
          });
        }
      }
    });
    port.onDisconnect.addListener(() => {
      console.log("Streaming port disconnected");
    });
  }
});
async function saveExtensionConfig(config) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set({ carbonlens_config: config }, () => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve();
      }
    });
  });
}
setInterval(() => {
  if (container?.agentRunner) {
    container.agentRunner.cleanupCompletedTasks();
  }
}, 60 * 60 * 1e3);
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("CarbonLens extension installed");
    saveExtensionConfig({
      useRealMode: false,
      notificationChannels: []
    });
  }
});
