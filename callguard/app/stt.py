"""Streaming speech-to-text providers and audio session management."""
import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Optional
import websockets

logger = logging.getLogger("callguard.stt")


@dataclass
class TranscriptResult:
    text: str
    speaker: str
    is_final: bool
    channel: int = 0
    confidence: float = 1.0


class AudioStreamSession(ABC):
    """Active streaming STT session."""

    @abstractmethod
    async def send_audio(self, pcm_chunk: bytes) -> None:
        """Send raw 16 kHz PCM chunk."""
        ...

    @abstractmethod
    async def finish(self) -> None:
        """Signal end of audio stream."""
        ...

    @abstractmethod
    def receive(self) -> AsyncIterator[TranscriptResult]:
        """Stream transcription results."""
        ...


class STTProvider(ABC):
    """Abstract speech-to-text provider interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    async def create_stream(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        channel_mapping: Optional[Dict[int, str]] = None,
    ) -> AudioStreamSession:
        ...


class DeepgramStreamingSession(AudioStreamSession):
    def __init__(
        self,
        api_key: str,
        sample_rate: int = 16000,
        channels: int = 1,
        channel_mapping: Optional[Dict[int, str]] = None,
    ):
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.channels = channels
        self.channel_mapping = channel_mapping or {0: "Agent", 1: "Customer"}
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._queue: asyncio.Queue[Optional[TranscriptResult]] = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
        self._closed = False

    async def connect(self):
        query = (
            f"encoding=linear16&sample_rate={self.sample_rate}&channels={self.channels}"
            f"&punctuate=true&smart_format=true&interim_results=true"
        )
        if self.channels > 1:
            query += "&multichannel=true"

        url = f"wss://api.deepgram.com/v1/listen?{query}"
        headers = {"Authorization": f"Token {self.api_key}"}

        # websockets connect compatibility
        try:
            self.ws = await websockets.connect(url, additional_headers=headers)
        except TypeError:
            # Fallback for older websockets versions if any
            self.ws = await websockets.connect(url, extra_headers=headers)

        self._reader_task = asyncio.create_task(self._listen_loop())

    async def _listen_loop(self):
        try:
            while not self._closed and self.ws:
                try:
                    msg = await self.ws.recv()
                except websockets.exceptions.ConnectionClosed:
                    break
                if not msg:
                    continue
                data = json.loads(msg)
                if data.get("type") == "Results":
                    channel_idx = 0
                    if "channel_index" in data and data["channel_index"]:
                        channel_idx = data["channel_index"][0]

                    alts = data.get("channel", {}).get("alternatives", [])
                    if alts:
                        alt = alts[0]
                        transcript = alt.get("transcript", "").strip()
                        if transcript:
                            is_final = bool(data.get("is_final") or data.get("speech_final"))
                            speaker = self.channel_mapping.get(
                                channel_idx,
                                "Agent" if channel_idx == 0 else "Customer"
                            )
                            await self._queue.put(
                                TranscriptResult(
                                    text=transcript,
                                    speaker=speaker,
                                    is_final=is_final,
                                    channel=channel_idx,
                                    confidence=float(alt.get("confidence", 1.0)),
                                )
                            )
        except Exception as e:
            logger.error("Deepgram listen loop error: %s", e)
        finally:
            await self._queue.put(None)

    async def send_audio(self, pcm_chunk: bytes) -> None:
        if self.ws and not self._closed:
            await self.ws.send(pcm_chunk)

    async def finish(self) -> None:
        self._closed = True
        if self.ws:
            try:
                # Deepgram signals end of stream with empty frame or CloseStream
                await self.ws.send(json.dumps({"type": "CloseStream"}))
                await asyncio.sleep(0.1)
                await self.ws.close()
            except Exception:
                pass
        if self._reader_task:
            await self._reader_task

    async def receive(self) -> AsyncIterator[TranscriptResult]:
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item


class DeepgramSTTProvider(STTProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("DEEPGRAM_API_KEY", "").strip()

    @property
    def name(self) -> str:
        return "deepgram"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def create_stream(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        channel_mapping: Optional[Dict[int, str]] = None,
    ) -> AudioStreamSession:
        if not self.is_available:
            raise RuntimeError("DEEPGRAM_API_KEY is not set.")
        session = DeepgramStreamingSession(
            api_key=self._api_key,
            sample_rate=sample_rate,
            channels=channels,
            channel_mapping=channel_mapping,
        )
        await session.connect()
        return session


class BrowserFallbackSTTProvider(STTProvider):
    """Fallback provider when server-side Deepgram is not configured."""

    @property
    def name(self) -> str:
        return "browser_fallback"

    @property
    def is_available(self) -> bool:
        # Browser recognition happens client-side via Web Speech API
        return True

    async def create_stream(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        channel_mapping: Optional[Dict[int, str]] = None,
    ) -> AudioStreamSession:
        raise NotImplementedError(
            "BrowserFallbackSTTProvider processes speech in the browser via Web Speech API."
        )


class MockStreamingSession(AudioStreamSession):
    """Session for unit testing STT audio websocket pipelines."""

    def __init__(self, channel_mapping: Optional[Dict[int, str]] = None):
        self.channel_mapping = channel_mapping or {0: "Agent", 1: "Customer"}
        self._queue: asyncio.Queue[Optional[TranscriptResult]] = asyncio.Queue()
        self.received_audio_bytes = 0

    async def send_audio(self, pcm_chunk: bytes) -> None:
        self.received_audio_bytes += len(pcm_chunk)
        # Yield a mock transcript once enough bytes arrive for testing
        if self.received_audio_bytes >= 3200 and self.received_audio_bytes < 6400:
            await self._queue.put(
                TranscriptResult(
                    text="This fund is risk-free",
                    speaker=self.channel_mapping.get(0, "Advisor"),
                    is_final=True,
                    channel=0,
                )
            )

    async def finish(self) -> None:
        await self._queue.put(None)

    async def receive(self) -> AsyncIterator[TranscriptResult]:
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item


class MockSTTProvider(STTProvider):
    @property
    def name(self) -> str:
        return "mock"

    @property
    def is_available(self) -> bool:
        return True

    async def create_stream(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        channel_mapping: Optional[Dict[int, str]] = None,
    ) -> AudioStreamSession:
        return MockStreamingSession(channel_mapping=channel_mapping)


def get_stt_provider(provider_name: Optional[str] = None) -> STTProvider:
    """Factory to get the requested or default STT provider."""
    name = (provider_name or os.getenv("CALLGUARD_STT_PROVIDER", "auto")).lower()
    if name == "mock":
        return MockSTTProvider()
    if name == "deepgram":
        return DeepgramSTTProvider()
    if name == "browser" or name == "browser_fallback":
        return BrowserFallbackSTTProvider()

    # 'auto': Deepgram if API key present, otherwise fallback
    dg = DeepgramSTTProvider()
    return dg if dg.is_available else BrowserFallbackSTTProvider()
