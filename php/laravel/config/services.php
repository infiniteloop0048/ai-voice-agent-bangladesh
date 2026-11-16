<?php

// Merge this entry into the existing services config so other services stay configured.
return [
    'voice' => [
        'url' => env('VOICE_API_URL'),
        'key' => env('VOICE_API_KEY'),
        'secret' => env('VOICE_WEBHOOK_SECRET'),
    ],
];
