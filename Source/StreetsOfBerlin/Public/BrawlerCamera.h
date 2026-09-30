#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BrawlerCamera.generated.h"

class UCameraComponent;

/** Orthografische Seitenkamera mit 2D-tauglichen Post-Process-Einstellungen. */
UCLASS()
class STREETSOFBERLIN_API ABrawlerCamera : public AActor
{
	GENERATED_BODY()

public:
	ABrawlerCamera();

	void SetView(float X, float ShakeX, float ShakeZ);

	UPROPERTY(VisibleAnywhere, Category = "Brawler")
	TObjectPtr<UCameraComponent> Camera;
};
