# app.py

from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import html
from utils import generate_fake_paper
import urllib3
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from utils import generate_fake_paper, analyze_paper_content


urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Important for flash messages

# Use global variables to store the generated paper and format choice
generated_paper = None
output_format = "pdf"


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_paper():
    global generated_paper, output_format

    try:
        user_input = request.form.get('user_input')
        output_format = request.form.get('output_format', 'pdf')

        if not user_input or not user_input.strip():
            flash('Please enter a topic for your paper.', 'error')
            return redirect(url_for('home'))

        # Generate the full paper using the updated utility function
        generated_paper = generate_fake_paper(user_input=user_input)

        # Check if generation resulted in an error
        if "error" in generated_paper:
            flash(f'Error generating paper: {generated_paper["error"]}', 'error')
            return redirect(url_for('home'))

        return render_template('preview.html', paper=generated_paper, format=output_format)

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred in /generate: {e}")
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('home'))


def sanitize_for_reportlab(text):
    """Escapes special characters to prevent ReportLab from crashing."""
    return html.escape(text)

@app.route('/analyzer')
def analyzer_page():
    """Renders the standalone content analyzer page."""
    return render_template('analyzer.html')


@app.route('/analyze', methods=['POST'])
def analyze_paper():
    """
    Receives paper text from the frontend, analyzes it, and returns the result.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided for analysis.'}), 400

    paper_text = data['text']

    # Call the new analysis function from utils.py
    analysis_result = analyze_paper_content(paper_text)

    if "score" in analysis_result and analysis_result["score"] == -1:
        return jsonify({'error': analysis_result['reasoning']}), 500

    return jsonify(analysis_result)

@app.route('/download')
def download():
    global generated_paper, output_format

    if not generated_paper:
        flash('No paper has been generated yet. Please generate one first.', 'error')
        return redirect(url_for('home'))

    current_format = request.args.get('format', output_format)
    print(f"[DEBUG] Starting download process for format: {current_format}")

    try:
        if current_format == 'pdf':
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer)
            styles = getSampleStyleSheet()

            # CORRECTED: Create new ParagraphStyle objects and add them
            styles.add(ParagraphStyle(name='TitleStyle', parent=styles['Title'], alignment=TA_CENTER, fontSize=24))
            styles.add(ParagraphStyle(name='AuthorStyle', parent=styles['Normal'], alignment=TA_CENTER,
                                      fontName='Helvetica-Oblique', spaceAfter=24))
            styles.add(ParagraphStyle(name='BodyStyle', parent=styles['BodyText'], alignment=TA_JUSTIFY, spaceAfter=12))
            styles.add(ParagraphStyle(name='HeadingStyle', parent=styles['h2'], spaceAfter=6))

            elements = []

            # Sanitize all AI-generated content before adding it
            title = sanitize_for_reportlab(generated_paper.get('title', 'Untitled'))
            authors = sanitize_for_reportlab(generated_paper.get('authors', 'Anonymous'))
            abstract = sanitize_for_reportlab(generated_paper.get('abstract', ''))

            # Use the new custom styles
            elements.append(Paragraph(title, styles['TitleStyle']))
            elements.append(Paragraph(authors, styles['AuthorStyle']))

            elements.append(Paragraph("Abstract", styles['HeadingStyle']))
            elements.append(Paragraph(abstract, styles['BodyStyle']))

            for section in generated_paper.get('sections', []):
                heading = sanitize_for_reportlab(section.get('heading', ''))
                content = sanitize_for_reportlab(section.get('content', '')).replace('\n', '<br/>\n')

                elements.append(Paragraph(heading, styles['HeadingStyle']))
                elements.append(Paragraph(content, styles['BodyStyle']))

            print("[DEBUG] Building PDF document...")
            doc.build(elements)
            print("[DEBUG] PDF build successful.")

            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='generated_paper.pdf',
                             mimetype='application/pdf')

        elif current_format == 'latex':
            # This part remains the same
            def escape_latex(text):
                return text.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#').replace('_',
                                                                                                                    '\\_').replace(
                    '{', '\\{').replace('}', '\\}').replace('~', '\\textasciitilde{}').replace('^',
                                                                                               '\\textasciicircum{}')

            title = escape_latex(generated_paper.get('title', 'Untitled'))
            authors = escape_latex(generated_paper.get('authors', 'Anonymous'))
            abstract = escape_latex(generated_paper.get('abstract', ''))

            sections_content = ""
            for section in generated_paper.get('sections', []):
                heading = escape_latex(section.get('heading', ''))
                if heading.lower() == 'references':
                    sections_content += f"\\section*{{{heading}}}\n\\begin{{verbatim}}\n{section.get('content', '')}\n\\end{{verbatim}}\n\n"
                else:
                    content = escape_latex(section.get('content', ''))
                    sections_content += f"\\section*{{{heading}}}\n{content}\n\n"

            latex_content = f"""\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\title{{{title}}}
\\author{{{authors}}}
\\date{{\\today}}
\\begin{{document}}
\\maketitle
\\begin{{abstract}}
{abstract}
\\end{{abstract}}
{sections_content}
\\end{{document}}
"""
            buffer = io.BytesIO(latex_content.encode('utf-8'))
            return send_file(buffer, as_attachment=True, download_name='generated_paper.tex',
                             mimetype='application/x-tex')

    except Exception as e:
        print(f"[ERROR] CRITICAL: Failed to create download file: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error creating the download file. Please check the console for details.', 'error')
        return redirect(url_for('preview'))

@app.route('/preview')
def preview():
    global generated_paper, output_format
    if not generated_paper:
        flash('No paper has been generated yet. Please create one first.', 'error')
        return redirect(url_for('home'))
    return render_template('preview.html', paper=generated_paper, format=output_format)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5003)