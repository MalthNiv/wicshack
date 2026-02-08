export class StockAnimator {
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;
    private prices: number[] = [];
    private frameProgress: number = 0;
   
    private audioCtx: AudioContext | null = null;
    private analyser: AnalyserNode | null = null;
    private dataArray!: Uint8Array<ArrayBuffer>;
    private lastIntensity: number = 0;
    private animationId: number | null = null;


    private readonly width = 800;
    private readonly height = 400;
    private readonly padding = 60;


    constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        this.ctx = this.canvas.getContext('2d')!;
        this.setupHighDPI();
    }


    private setupHighDPI() {
        const dpr = window.devicePixelRatio || 1;
        const width = 800;
        const height = 400;
       
        this.canvas.width = width * dpr;
        this.canvas.height = height * dpr;
        this.canvas.style.width = `${width}px`;
        this.canvas.style.height = `${height}px`;
        this.ctx.scale(dpr, dpr);
    }


    // Call this to initialize data and audio
    public async start(prices: number[], audioSource: HTMLAudioElement) {
        this.prices = prices;
        this.setupAudio(audioSource);
        this.animate();
    }


    private setupAudio(audio: HTMLAudioElement) {
        this.audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const source = this.audioCtx.createMediaElementSource(audio);
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 256;


        source.connect(this.analyser);
        this.analyser.connect(this.audioCtx.destination);


        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    }


    private getBeatIntensity(): number {
        if (!this.analyser || !this.dataArray) return 0;
        this.analyser.getByteFrequencyData(this.dataArray);
        const bass = this.dataArray.slice(0, 10).reduce((a, b) => a + b, 0) / 10;
        // Smoothing: prevents the jitter from being too harsh
        this.lastIntensity = this.lastIntensity * 0.8 + bass * 0.2;
        return this.lastIntensity;
    }


    private animate = () => {
        const intensity = this.getBeatIntensity();
       
        // Speed sync: Base movement + audio surge
        const speedBoost = (intensity / 255) * 0.25;
        this.frameProgress += 0.03 + speedBoost;


        this.draw(intensity);


        if (this.frameProgress < this.prices.length - 1) {
            requestAnimationFrame(this.animate);
        }
    }

    public stop() {
        if (this.animationId) cancelAnimationFrame(this.animationId); 
        if (this.audioCtx) this.audioCtx.close(); 
    }

    private draw(intensity: number) {
        const { ctx, prices, width, height, padding, frameProgress } = this;
       
        ctx.clearRect(0, 0, width, height);


        const min = Math.min(...prices);
        const max = Math.max(...prices);
        const range = (max - min) || 1;
        const spacing = (width - (padding * 2)) / (prices.length - 1);


        // Helper for coordinate mapping
        const getX = (i: number) => padding + (i * spacing);
        const getY = (p: number) => height - padding - ((p - min) / range) * (height - padding * 2);


        // Music-reactive styling
        const glowSize = 5 + (intensity / 255) * 20;
        const lineWidth = 3 + (intensity / 255) * 4;


        // 1. Draw completed segments
        for (let i = 1; i < frameProgress; i++) {
            const x1 = getX(i - 1), y1 = getY(prices[i - 1]);
            const x2 = getX(i), y2 = getY(prices[i]);


            ctx.beginPath();
            ctx.lineWidth = lineWidth;
            ctx.lineJoin = 'round';
            ctx.lineCap = 'round';
           
            const color = prices[i] >= prices[i-1] ? '#5BB8F5' : '#C4447A';
            ctx.strokeStyle = color;
            ctx.shadowBlur = glowSize;
            ctx.shadowColor = color;


            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }


        // 2. Draw growing tip
        const idx = Math.floor(frameProgress);
        if (idx < prices.length - 1) {
            const pct = frameProgress % 1;
            const x1 = getX(idx), y1 = getY(prices[idx]);
            const x2 = getX(idx + 1), y2 = getY(prices[idx + 1]);


            const curX = x1 + (x2 - x1) * pct;
            const curY = y1 + (y2 - y1) * pct;


            ctx.beginPath();
            ctx.strokeStyle = prices[idx + 1] >= prices[idx] ? '#00ffcc' : '#ff4444';
            ctx.moveTo(x1, y1);
            ctx.lineTo(curX, curY);
            ctx.stroke();
        }
    }
}
