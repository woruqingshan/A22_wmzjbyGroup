import { createAudioTurnRecorder } from "../audio/audioTurnRecorder";
import { VOICE_TURN_STATE } from "../audio/recorderStates";

export function createInputBar({ onSend, onStatusChange }) {
  const element = document.createElement("section");
  element.className = "input-panel";
  element.innerHTML = `
    <div class="panel-heading">
      <div>
        <p class="eyebrow">C · Input</p>
        <h2>Text / Audio Entry</h2>
      </div>
      <span class="chip">Audio-first scaffold</span>
    </div>
    <form class="input-form">
      <label class="field-label" for="message-box">Text message</label>
      <textarea id="message-box" rows="5" placeholder="Type a supportive conversation prompt or record audio."></textarea>
      <div class="input-actions">
        <button type="submit" class="primary-button" data-role="send-button">Send turn</button>
      </div>
      <button type="button" class="audio-turn-button" data-role="voice-button" aria-pressed="false">
        <span class="audio-turn-title" data-role="voice-title">Start voice input</span>
        <span class="audio-turn-meta" data-role="voice-meta">Use the microphone for one audio-only turn. Click again to stop and submit.</span>
      </button>
    </form>
  `;

  const form = element.querySelector(".input-form");
  const messageBox = element.querySelector("#message-box");
  const sendButton = element.querySelector('[data-role="send-button"]');
  const voiceButton = element.querySelector('[data-role="voice-button"]');
  const voiceTitle = element.querySelector('[data-role="voice-title"]');
  const voiceMeta = element.querySelector('[data-role="voice-meta"]');

  const recorder = createAudioTurnRecorder();

  let isBusy = false;
  let voiceTurnState = VOICE_TURN_STATE.IDLE;
  let preservedDraft = "";

  function syncControls() {
    const textLocked = isBusy || voiceTurnState !== VOICE_TURN_STATE.IDLE;

    messageBox.disabled = textLocked;
    sendButton.disabled = textLocked;
    sendButton.textContent = isBusy ? "Sending..." : "Send turn";

    voiceButton.disabled = voiceTurnState === VOICE_TURN_STATE.PROCESSING
      || (isBusy && voiceTurnState !== VOICE_TURN_STATE.RECORDING);
    voiceButton.dataset.state = voiceTurnState;
    voiceButton.setAttribute("aria-pressed", String(voiceTurnState === VOICE_TURN_STATE.RECORDING));

    if (voiceTurnState === VOICE_TURN_STATE.RECORDING) {
      voiceTitle.textContent = "Stop voice input";
      voiceMeta.textContent = "Recording from the microphone. Text input is locked until this voice turn finishes.";
      messageBox.placeholder = "Voice capture in progress. This turn will be sent as audio only.";
      return;
    }

    if (voiceTurnState === VOICE_TURN_STATE.PROCESSING) {
      voiceTitle.textContent = "Processing voice input";
      voiceMeta.textContent = "Preparing the recorded audio and sending the voice turn to the local edge-backend.";
      messageBox.placeholder = "Voice turn is being processed.";
      return;
    }

    voiceTitle.textContent = "Start voice input";
    voiceMeta.textContent = "Use the microphone for one audio-only turn. Click again to stop and submit.";
    messageBox.placeholder = "Type a supportive conversation prompt or record audio.";
  }

  async function startVoiceTurn() {
    preservedDraft = messageBox.value;
    voiceTurnState = VOICE_TURN_STATE.RECORDING;
    messageBox.value = "";
    syncControls();

    try {
      await recorder.start();
      onStatusChange("Recording audio from microphone. Text input is locked for this turn.");
    } catch (error) {
      voiceTurnState = VOICE_TURN_STATE.IDLE;
      messageBox.value = preservedDraft;
      preservedDraft = "";
      syncControls();

      const detail = error instanceof Error ? error.message : "Audio capture failed.";
      onStatusChange(detail);
    }
  }

  async function stopVoiceTurn() {
    voiceTurnState = VOICE_TURN_STATE.PROCESSING;
    syncControls();
    onStatusChange("Stopping microphone capture and preparing the voice turn.");

    try {
      const audioPayload = await recorder.stop();
      if (!audioPayload?.audio_base64) {
        throw new Error("No audio data was captured for this voice turn.");
      }

      const sent = await onSend({
        text: "",
        audio: audioPayload,
      });

      if (!sent) {
        messageBox.value = preservedDraft;
      }

      preservedDraft = "";
    } catch (error) {
      messageBox.value = preservedDraft;
      preservedDraft = "";

      const detail = error instanceof Error ? error.message : "Voice turn processing failed.";
      onStatusChange(detail);
    } finally {
      voiceTurnState = VOICE_TURN_STATE.IDLE;
      syncControls();
    }
  }

  function setBusy(nextBusy) {
    isBusy = nextBusy;
    syncControls();
  }

  voiceButton.addEventListener("click", async () => {
    if (voiceTurnState === VOICE_TURN_STATE.RECORDING) {
      await stopVoiceTurn();
      return;
    }

    if (voiceTurnState === VOICE_TURN_STATE.IDLE) {
      await startVoiceTurn();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const sent = await onSend({
      text: messageBox.value.trim(),
      audio: null,
    });
    if (sent) {
      messageBox.value = "";
      onStatusChange("Input cleared and ready for the next turn.");
    }
  });

  syncControls();

  return {
    element,
    setBusy,
  };
}
