'use client';

export default function LoadingIndicator({ text = 'Cargando...', size = 'md' }: {
    text?: string;
    size?: 'sm' | 'md' | 'lg';
}) {
    const sizes = {
        sm: 'w-10 h-10',
        md: 'w-16 h-16',
        lg: 'w-24 h-24'
    };

    return (
        <div className="flex flex-col items-center justify-center gap-4 p-8">
            <div className={`${sizes[size]} relative animate-pulse`}>
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-satellite-blue to-satellite-deep opacity-20" />
                <div className="absolute inset-2 rounded-full bg-white" />
                <div className="absolute inset-4 rounded-full bg-gradient-to-r from-data-accent to-data-purple animate-spin" />
            </div>
            {text && <p className="text-sm font-semibold text-satellite-deep">{text}</p>}
        </div>
    );
}
