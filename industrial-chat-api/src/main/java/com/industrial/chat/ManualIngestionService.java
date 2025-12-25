package com.industrial.chat;

import org.springframework.ai.reader.pdf.PagePdfDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Component;
import org.springframework.ai.document.Document;

import java.util.List;

@Component
public class ManualIngestionService {

    private final VectorStore vectorStore;

    public ManualIngestionService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    public void loadManual(Resource pdfResource) {
        // 1. Read the PDF
        PagePdfDocumentReader pdfReader = new PagePdfDocumentReader(pdfResource);
<<<<<<< HEAD

        // 2. Split it into readable chunks (e.g., paragraphs)
        TokenTextSplitter splitter = new TokenTextSplitter();
        List<Document> chunks = splitter.apply(pdfReader.get());

=======

        // 2. Split it into readable chunks (e.g., paragraphs)
        TokenTextSplitter splitter = new TokenTextSplitter();
        List<Document> chunks = splitter.apply(pdfReader.get());

>>>>>>> c00699664d3818edf437bf12f56f434451084e1b
        // 3. Save to the Vault
        vectorStore.add(chunks);
        System.out.println("Manual successfully indexed into the Vault.");
    }
}
