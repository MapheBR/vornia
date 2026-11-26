import Image from "next/image";

interface BrandLogoProps {
  width?: number;
  className?: string;
}

/** Logo oficial da Vornia (assets em branding/logo.png, 2172x724). */
export function BrandLogo({ width = 180, className }: BrandLogoProps) {
  return (
    <Image
      src="/logo.png"
      alt="Vornia"
      width={width}
      height={Math.round(width / 3)}
      className={className}
      priority
    />
  );
}
