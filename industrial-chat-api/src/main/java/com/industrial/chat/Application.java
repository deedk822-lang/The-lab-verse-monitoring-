package com.industrial.chat;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;

import java.net.URL;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    public CommandLineRunner dataLoader(ManualIngestionService ingestionService) {
        return args -> {
            System.out.println("--- LOADING SAMPLE MANUAL ---");
            // In a real application, you would get this from a file upload or a directory
            try {
                // Using a placeholder PDF for demonstration purposes
                Resource pdfResource = new UrlResource("https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf");
                ingestionService.loadManual(pdfResource);
                System.out.println("--- SAMPLE MANUAL LOADED ---");
            } catch (Exception e) {
                System.err.println("Failed to load sample PDF. The ingestion service is ready, but you will need to load manuals manually.");
                e.printStackTrace();
            }
        };
    }
}
