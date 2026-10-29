import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "NaEscola",
  description: "Currículo, linhas do tempo e aulas dos anos iniciais e do 6º ano.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <a className="skip" href="#conteudo">Ir para o conteúdo</a>
        <header className="site-header">
          <div className="wrap">
            <Link className="brand" href="/">
              <strong>NaEscola</strong>
              <span>Conhecimento em sequência</span>
            </Link>
            <nav aria-label="Principal">
              <Link href="/">Início</Link>
              <Link href="/">Busca</Link>
              <Link href="/competencias">Competências</Link>
            </nav>
          </div>
        </header>
        <main id="conteudo" className="wrap">{children}</main>
        <footer className="site-footer">
          <div className="wrap">
            <p>Os códigos e os enunciados vêm da BNCC ou do complemento de Computação de 2022. A ordem das aulas é uma proposta da NaEscola.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
