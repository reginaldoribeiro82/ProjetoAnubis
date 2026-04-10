import streamlit as st
import pdfplumber
import re
import io
import zipfile
from docxtpl import DocxTemplate

# ==========================================
# CONFIGURAÇÃO E INTERFACE
# ==========================================
# Alterado o ícone da página para a Ankh (cruz do anúbis)
st.set_page_config(page_title="Anubis - Automação", page_icon="☥")

# Título com o novo símbolo ☥
st.title("Bem-vindo ao Anubis ☥")
st.write("Processamento de Relatórios GC-FID para Dosagem Alcoólica.")

pdf_file = st.file_uploader("Suba o Relatório de Amostras (PDF)", type=["pdf"])
docx_file = st.file_uploader("Suba o Molde do Laudo (.docx)", type=["docx"])

if pdf_file and docx_file:
    if st.button("🚀 Processar Laudos", type="primary"):
        
        with st.spinner("Processando amostras e gerando arquivos..."):
            amostras_extraidas = {}

            with pdfplumber.open(pdf_file) as pdf:
                for pagina in pdf.pages:
                    texto = pagina.extract_text()
                    if not texto: continue
                    
                    match_amostra = re.search(r"(\d+-\d+)-([12])", texto)
                    
                    if match_amostra:
                        rg_ano_original = match_amostra.group(1) 
                        rg_ano_interno = rg_ano_original.replace("-", "/")
                        
                        match_etanol = re.search(r"Etanol.*?\s+([\d,]+)\s*\n", texto)
                        valor_etanol = float(match_etanol.group(1).replace(",", ".")) if match_etanol else 0.0
                        
                        if rg_ano_interno not in amostras_extraidas:
                            amostras_extraidas[rg_ano_interno] = []
                        amostras_extraidas[rg_ano_interno].append(valor_etanol)

            # ==========================================
            # GERAÇÃO DOS ARQUIVOS E ZIP
            # ==========================================
            zip_buffer = io.BytesIO()
            lista_arquivos_para_download = []
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for identificacao, valores in amostras_extraidas.items():
                    
                    media_dgL = sum(valores) / len(valores)
                    
                    if media_dgL > 3.0:
                        resultado_texto = f"PQT: {media_dgL:.1f} dg/L."
                        mostrar_tabela = True
                    else:
                        resultado_texto = "Pelos exames cromatográficos efetuados, NÃO se constatou a presença de etanol na amostra analisada."
                        mostrar_tabela = False

                    # Nome do arquivo conforme solicitado: Laudo_120_26.docx
                    nome_arquivo_word = f"Laudo_{identificacao.replace('/', '_')}.docx"

                    doc = DocxTemplate(docx_file)
                    contexto = {
                        "RESULTADO_TEXTO": resultado_texto,
                        "mostrar_tabela": mostrar_tabela,
                        "NOME_AMOSTRA": identificacao 
                    }
                    doc.render(contexto)
                    
                    output = io.BytesIO()
                    doc.save(output)
                    conteudo_arquivo = output.getvalue()
                    
                    zip_file.writestr(nome_arquivo_word, conteudo_arquivo)
                    lista_arquivos_para_download.append({
                        "nome": nome_arquivo_word,
                        "buffer": conteudo_arquivo
                    })

            st.success(f"Sucesso! {len(amostras_extraidas)} amostras processadas.")
            
            st.download_button(
                label="📦 Baixar Todos os Laudos (ZIP)",
                data=zip_buffer.getvalue(),
                file_name="Anubis_Resultados.zip",
                mime="application/zip",
                type="primary"
            )

            st.divider()
            st.write("Downloads individuais:")
            for arq in lista_arquivos_para_download:
                st.download_button(
                    label=f"📄 {arq['nome']}",
                    data=arq['buffer'],
                    file_name=arq['nome'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=arq['nome']
                )

# ==========================================
# RODAPÉ (FIM DA TELA)
# ==========================================
st.markdown("---")
st.caption("Powered by Reginaldo Ribeiro")
