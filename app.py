import streamlit as st
import pdfplumber
import re
import io
import zipfile
from docxtpl import DocxTemplate

# ==========================================
# INTERFACE DO ANUBIS
# ==========================================
st.set_page_config(page_title="Anubis - Automação", page_icon="⚖️")

st.title("Bem-vindo ao Anubis ⚖️")
st.markdown("### Ferramenta de automação de laudos by Reginaldo Ribeiro")
st.write("Processamento de Relatórios GC-FID para Dosagem Alcoólica.")

pdf_file = st.file_uploader("Suba o Relatório de Amostras (PDF)", type=["pdf"])
docx_file = st.file_uploader("Suba o Molde do Laudo (.docx)", type=["docx"])

if pdf_file and docx_file:
    amostras_extraidas = {}

    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            # Identifica amostras e ignora Brancos/Controles
            match_amostra = re.search(r"(\d+-\d+)-([12])", texto)
            
            if match_amostra:
                # ALTERAÇÃO AQUI: Captura o valor e troca o hífen pela barra
                rg_ano_original = match_amostra.group(1) 
                rg_ano_formatado = rg_ano_original.replace("-", "/") # Transforma 120-26 em 120/26
                
                # Busca concentração de Etanol
                match_etanol = re.search(r"Etanol.*?\s+([\d,]+)\s*\n", texto)
                valor_etanol = float(match_etanol.group(1).replace(",", ".")) if match_etanol else 0.0
                
                if rg_ano_formatado not in amostras_extraidas:
                    amostras_extraidas[rg_ano_formatado] = []
                amostras_extraidas[rg_ano_formatado].append(valor_etanol)

    # ==========================================
    # PROCESSAMENTO E GERAÇÃO DOS LAUDOS
    # ==========================================
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for identificacao, valores in amostras_extraidas.items():
            
            # Média das duplicatas
            media_dgL = sum(valores) / len(valores)
            
            # LÓGICA DE LAUDO (Padronizado conforme sua orientação)
            if media_dgL > 3.0:
                # Reportado apenas em dg/L conforme padrão do laboratório
                resultado_texto = f"PQT: {media_dgL:.1f} dg/L."
                mostrar_tabela = True
            else:
                # Frase solicitada para casos negativos
                resultado_texto = "Pelos exames cromatográficos efetuados, NÃO se constatou a presença de etanol na amostra analisada."
                mostrar_tabela = False

            # Injeção no Word
            doc = DocxTemplate(docx_file)
            contexto = {
                "RESULTADO_TEXTO": resultado_texto,
                "mostrar_tabela": mostrar_tabela,
                "NOME_AMOSTRA": identificacao # Enviará "120/26"
            }
            doc.render(contexto)
            
            output = io.BytesIO()
            doc.save(output)
            zip_file.writestr(f"Laudo_{identificacao.replace('/', '_')}.docx", output.getvalue())

    st.success(f"Sucesso! {len(amostras_extraidas)} amostras processadas.")
    st.download_button(
        label="⬇️ Baixar Todos os Laudos (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="Anubis_Resultados.zip",
        mime="application/zip",
        type="primary"
    )
